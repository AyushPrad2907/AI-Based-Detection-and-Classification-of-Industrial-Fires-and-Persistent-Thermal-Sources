"""
SIH26162 — Feature Engineering Pipeline.

Transforms raw and processed NASA FIRMS satellite observations and geospatial context
into structured, normalized, multi-dimensional feature representations for ML classification
and persistent thermal source detection.
"""

import logging
import math
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Standard ordered list of core numerical features used across models
DEFAULT_FEATURE_COLUMNS: List[str] = [
    # Thermal features
    "brightness_primary",
    "brightness_secondary",
    "brightness_diff",
    "brightness_ratio",
    "frp",
    "log_frp",
    "confidence_score",
    "frp_density",
    # Temporal features
    "hour",
    "is_night",
    "solar_hour_approx",
    "day_of_week",
    "is_weekend",
    "month",
    "sin_hour",
    "cos_hour",
    "sin_month",
    "cos_month",
    # Spatial & Sensor features
    "latitude",
    "longitude",
    "scan",
    "track",
    "pixel_area_approx",
    "is_viirs",
    "is_modis",
    # Contextual / Industrial features
    "dist_to_industrial_km",
    "is_near_industrial",
    "persistence_count",
    "persistence_days",
]


class FeatureBuilder:
    """
    Constructs feature matrices for machine learning models and spatial analytics.
    """

    def __init__(self, feature_columns: Optional[List[str]] = None):
        self.feature_columns = feature_columns or list(DEFAULT_FEATURE_COLUMNS)

    def extract_thermal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract thermal and spectral contrast features.
        """
        feats = pd.DataFrame(index=df.index)

        # Primary brightness (Kelvin)
        if "brightness_primary" in df.columns:
            feats["brightness_primary"] = pd.to_numeric(df["brightness_primary"], errors="coerce").fillna(300.0)
        elif "bright_ti4" in df.columns:
            feats["brightness_primary"] = pd.to_numeric(df["bright_ti4"], errors="coerce").fillna(300.0)
        elif "brightness" in df.columns:
            feats["brightness_primary"] = pd.to_numeric(df["brightness"], errors="coerce").fillna(300.0)
        else:
            feats["brightness_primary"] = pd.Series(300.0, index=df.index)

        # Secondary brightness (Kelvin)
        if "brightness_secondary" in df.columns:
            feats["brightness_secondary"] = pd.to_numeric(df["brightness_secondary"], errors="coerce").fillna(290.0)
        elif "bright_ti5" in df.columns:
            feats["brightness_secondary"] = pd.to_numeric(df["bright_ti5"], errors="coerce").fillna(290.0)
        elif "bright_t31" in df.columns:
            feats["brightness_secondary"] = pd.to_numeric(df["bright_t31"], errors="coerce").fillna(290.0)
        else:
            feats["brightness_secondary"] = pd.Series(290.0, index=df.index)

        # Spectral contrast: primary - secondary
        feats["brightness_diff"] = feats["brightness_primary"] - feats["brightness_secondary"]
        # Ratio
        feats["brightness_ratio"] = feats["brightness_primary"] / feats["brightness_secondary"].clip(lower=1.0)

        # FRP (Fire Radiative Power in MW)
        if "frp" in df.columns:
            feats["frp"] = pd.to_numeric(df["frp"], errors="coerce").fillna(0.0).clip(lower=0.0)
        else:
            feats["frp"] = pd.Series(0.0, index=df.index)

        feats["log_frp"] = np.log1p(feats["frp"])

        # Confidence (0 - 100)
        if "confidence_score" in df.columns:
            feats["confidence_score"] = pd.to_numeric(df["confidence_score"], errors="coerce").fillna(50.0).clip(0.0, 100.0)
        elif "confidence" in df.columns:
            def _map_c(val):
                if pd.isna(val):
                    return 50.0
                v = str(val).lower().strip()
                if v in ("l", "low"):
                    return 30.0
                if v in ("n", "nominal"):
                    return 70.0
                if v in ("h", "high"):
                    return 100.0
                try:
                    return float(val)
                except Exception:
                    return 50.0
            feats["confidence_score"] = df["confidence"].apply(_map_c).clip(0.0, 100.0)
        else:
            feats["confidence_score"] = pd.Series(50.0, index=df.index)

        return feats

    def extract_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract cyclic and calendar temporal features.
        """
        feats = pd.DataFrame(index=df.index)

        # Datetime resolution
        if "acq_datetime" in df.columns:
            dt_series = pd.to_datetime(df["acq_datetime"], errors="coerce")
        elif "acq_date" in df.columns:
            dt_series = pd.to_datetime(df["acq_date"], errors="coerce")
        else:
            dt_series = pd.Series(pd.Timestamp("2026-08-24 12:00:00"), index=df.index)

        # Fallback for NaT
        dt_series = dt_series.fillna(pd.Timestamp("2026-08-24 12:00:00"))

        feats["hour"] = dt_series.dt.hour + (dt_series.dt.minute / 60.0)
        feats["day_of_week"] = dt_series.dt.dayofweek.astype(float)
        feats["is_weekend"] = feats["day_of_week"].isin([5, 6]).astype(float)
        feats["month"] = dt_series.dt.month.astype(float)

        # Day/Night flag
        if "daynight" in df.columns:
            feats["is_night"] = df["daynight"].astype(str).str.upper().apply(
                lambda x: 1.0 if x == "N" else (0.0 if x == "D" else 0.5)
            )
        else:
            feats["is_night"] = feats["hour"].apply(lambda h: 1.0 if (h >= 18.0 or h < 6.0) else 0.0)

        # Approximate Solar Local Time
        if "longitude" in df.columns:
            lon = pd.to_numeric(df["longitude"], errors="coerce").fillna(0.0)
        else:
            lon = pd.Series(0.0, index=df.index)
        feats["solar_hour_approx"] = (feats["hour"] + (lon / 15.0)) % 24.0

        # Cyclical transformations
        feats["sin_hour"] = np.sin(2.0 * np.pi * feats["hour"] / 24.0)
        feats["cos_hour"] = np.cos(2.0 * np.pi * feats["hour"] / 24.0)
        feats["sin_month"] = np.sin(2.0 * np.pi * feats["month"] / 12.0)
        feats["cos_month"] = np.cos(2.0 * np.pi * feats["month"] / 12.0)

        return feats

    def extract_spatial_and_sensor_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract coordinates, sensor geometry, and resolution features.
        """
        feats = pd.DataFrame(index=df.index)

        if "latitude" in df.columns:
            feats["latitude"] = pd.to_numeric(df["latitude"], errors="coerce").fillna(0.0)
        else:
            feats["latitude"] = pd.Series(0.0, index=df.index)

        if "longitude" in df.columns:
            feats["longitude"] = pd.to_numeric(df["longitude"], errors="coerce").fillna(0.0)
        else:
            feats["longitude"] = pd.Series(0.0, index=df.index)

        # Scan & Track pixel footprint
        if "scan" in df.columns:
            feats["scan"] = pd.to_numeric(df["scan"], errors="coerce").fillna(0.375)
        else:
            feats["scan"] = pd.Series(0.375, index=df.index)

        if "track" in df.columns:
            feats["track"] = pd.to_numeric(df["track"], errors="coerce").fillna(0.375)
        else:
            feats["track"] = pd.Series(0.375, index=df.index)

        feats["pixel_area_approx"] = feats["scan"] * feats["track"]

        # Instrument flags
        if "instrument" in df.columns:
            instrument_str = df["instrument"].astype(str).str.upper()
        else:
            instrument_str = pd.Series("VIIRS", index=df.index)

        feats["is_viirs"] = instrument_str.str.contains("VIIRS").astype(float)
        feats["is_modis"] = instrument_str.str.contains("MODIS").astype(float)

        return feats

    def extract_contextual_features(
        self,
        df: pd.DataFrame,
        osm_contexts: Optional[Union[List[Dict[str, Any]], pd.DataFrame]] = None,
    ) -> pd.DataFrame:
        """
        Extract industrial proximity and persistence features.
        """
        feats = pd.DataFrame(index=df.index)

        # Industrial distance (km)
        if "dist_to_industrial_km" in df.columns:
            feats["dist_to_industrial_km"] = pd.to_numeric(df["dist_to_industrial_km"], errors="coerce").fillna(10.0)
        elif osm_contexts is not None:
            if isinstance(osm_contexts, pd.DataFrame) and "dist_to_industrial_km" in osm_contexts.columns:
                feats["dist_to_industrial_km"] = osm_contexts["dist_to_industrial_km"].fillna(10.0)
            elif isinstance(osm_contexts, list):
                dists = [ctx.get("min_distance_m", 10000.0) / 1000.0 if ctx else 10.0 for ctx in osm_contexts]
                feats["dist_to_industrial_km"] = dists
            else:
                feats["dist_to_industrial_km"] = pd.Series(10.0, index=df.index)
        else:
            feats["dist_to_industrial_km"] = pd.Series(10.0, index=df.index)

        feats["is_near_industrial"] = (feats["dist_to_industrial_km"] <= 2.0).astype(float)

        # Persistence metrics (if provided by clustering)
        if "persistence_count" in df.columns:
            feats["persistence_count"] = pd.to_numeric(df["persistence_count"], errors="coerce").fillna(1.0)
        else:
            feats["persistence_count"] = pd.Series(1.0, index=df.index)

        if "persistence_days" in df.columns:
            feats["persistence_days"] = pd.to_numeric(df["persistence_days"], errors="coerce").fillna(0.0)
        else:
            feats["persistence_days"] = pd.Series(0.0, index=df.index)

        return feats

    def build_features_df(
        self,
        df: pd.DataFrame,
        osm_contexts: Optional[Union[List[Dict[str, Any]], pd.DataFrame]] = None,
    ) -> pd.DataFrame:
        """
        Build complete feature DataFrame aligned with self.feature_columns.
        """
        if df.empty:
            return pd.DataFrame(columns=self.feature_columns)

        thermal_df = self.extract_thermal_features(df)
        temporal_df = self.extract_temporal_features(df)
        spatial_df = self.extract_spatial_and_sensor_features(df)
        context_df = self.extract_contextual_features(df, osm_contexts=osm_contexts)

        combined = pd.concat([thermal_df, temporal_df, spatial_df, context_df], axis=1)

        # Derived combined features
        combined["frp_density"] = combined["frp"] / combined["pixel_area_approx"].clip(lower=0.01)

        # Ensure all required feature columns exist and are ordered deterministically
        for col in self.feature_columns:
            if col not in combined.columns:
                combined[col] = 0.0

        return combined[self.feature_columns].copy()

    def build_single_feature_vector(
        self,
        record: Dict[str, Any],
        osm_context: Optional[Dict[str, Any]] = None,
    ) -> np.ndarray:
        """
        Build a single 1D numpy feature vector from a dictionary observation.
        """
        df_single = pd.DataFrame([record])
        contexts = [osm_context] if osm_context else None
        feat_df = self.build_features_df(df_single, osm_contexts=contexts)
        return feat_df.values[0]

    def build_spatial_features(self, latitude: float, longitude: float) -> Dict[str, float]:
        """Extract spatial coordinate features for a location."""
        return {
            "latitude": float(latitude),
            "longitude": float(longitude),
        }

    def build_temporal_features(self, timestamp: Union[str, pd.Timestamp]) -> Dict[str, float]:
        """Extract temporal components from a timestamp."""
        ts = pd.to_datetime(timestamp)
        hour = ts.hour + ts.minute / 60.0
        month = float(ts.month)
        return {
            "hour": hour,
            "day_of_week": float(ts.dayofweek),
            "is_weekend": 1.0 if ts.dayofweek in [5, 6] else 0.0,
            "month": month,
            "sin_hour": math.sin(2.0 * math.pi * hour / 24.0),
            "cos_hour": math.cos(2.0 * math.pi * hour / 24.0),
            "sin_month": math.sin(2.0 * math.pi * month / 12.0),
            "cos_month": math.cos(2.0 * math.pi * month / 12.0),
        }

    def build_feature_vector(
        self,
        firms_record: Dict[str, Any],
        osm_context: Optional[Dict[str, Any]] = None,
    ) -> List[float]:
        """Build a complete feature vector as a python list."""
        vec = self.build_single_feature_vector(firms_record, osm_context=osm_context)
        return [float(x) for x in vec]
