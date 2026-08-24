"""
SIH26162 — Persistent Thermal Source Detector.

Implements spatio-temporal clustering and analytics to detect and characterize
persistent industrial heat sources (smelters, flaring stacks, foundries, power plants)
versus transient landscape wildfires and agricultural burns.
"""

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

from ml.models.base_model import BaseModel
from ml.utils.geo_utils import (
    EARTH_RADIUS_METERS,
    calculate_cluster_centroid,
    haversine_distance,
)

logger = logging.getLogger(__name__)


class PersistentThermalCluster:
    """
    Data representation of a spatio-temporal thermal cluster.
    """

    def __init__(
        self,
        cluster_id: int,
        centroid_lat: float,
        centroid_lon: float,
        observation_count: int,
        first_seen: str,
        last_seen: str,
        duration_days: float,
        mean_frp: float,
        max_frp: float,
        mean_brightness: float,
        mean_confidence: float,
        night_ratio: float,
        spatial_radius_m: float,
        is_persistent: bool,
        records: Optional[List[Dict[str, Any]]] = None,
    ):
        self.cluster_id = cluster_id
        self.centroid_lat = centroid_lat
        self.centroid_lon = centroid_lon
        self.observation_count = observation_count
        self.first_seen = first_seen
        self.last_seen = last_seen
        self.duration_days = duration_days
        self.mean_frp = mean_frp
        self.max_frp = max_frp
        self.mean_brightness = mean_brightness
        self.mean_confidence = mean_confidence
        self.night_ratio = night_ratio
        self.spatial_radius_m = spatial_radius_m
        self.is_persistent = is_persistent
        self.records = records or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "centroid_latitude": round(self.centroid_lat, 5),
            "centroid_longitude": round(self.centroid_lon, 5),
            "observation_count": self.observation_count,
            "first_seen_utc": self.first_seen,
            "last_seen_utc": self.last_seen,
            "persistence_duration_days": round(self.duration_days, 2),
            "mean_frp_mw": round(self.mean_frp, 2),
            "max_frp_mw": round(self.max_frp, 2),
            "mean_brightness_kelvin": round(self.mean_brightness, 2),
            "mean_confidence": round(self.mean_confidence, 1),
            "night_observation_ratio": round(self.night_ratio, 3),
            "spatial_radius_meters": round(self.spatial_radius_m, 1),
            "is_persistent": self.is_persistent,
        }


class ThermalDetector(BaseModel):
    """
    Spatio-temporal clustering engine for persistent thermal anomaly identification.
    """

    def __init__(
        self,
        spatial_eps_meters: float = 1200.0,
        min_samples: int = 2,
        min_persistence_observations: int = 2,
        min_duration_days: float = 0.5,
    ):
        """
        Args:
            spatial_eps_meters: Maximum distance (meters) between points in a spatial cluster.
            min_samples: Minimum points to form a dense DBSCAN cluster.
            min_persistence_observations: Observations needed to classify as persistent source.
            min_duration_days: Minimum days between first and last detection to qualify as persistent.
        """
        self.spatial_eps_meters = spatial_eps_meters
        self.min_samples = min_samples
        self.min_persistence_observations = min_persistence_observations
        self.min_duration_days = min_duration_days
        self.clusters_: List[PersistentThermalCluster] = []

    def fit_predict_clusters(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[PersistentThermalCluster]]:
        """
        Cluster observations spatially and temporally using Haversine distance.

        Args:
            df: DataFrame containing ['latitude', 'longitude', 'acq_datetime', 'frp', ...].

        Returns:
            Tuple of (DataFrame with 'cluster_id' column, List of PersistentThermalCluster objects).
        """
        if df.empty:
            df_out = df.copy()
            df_out["cluster_id"] = []
            df_out["is_persistent_cluster"] = []
            self.clusters_ = []
            return df_out, []

        df_work = df.copy().reset_index(drop=True)

        # Coordinate arrays in radians for DBSCAN haversine metric
        coords_rad = np.radians(df_work[["latitude", "longitude"]].values)
        eps_rad = self.spatial_eps_meters / EARTH_RADIUS_METERS

        # Run DBSCAN
        db = DBSCAN(eps=eps_rad, min_samples=self.min_samples, metric="haversine")
        labels = db.fit_predict(coords_rad)

        df_work["cluster_id"] = labels
        df_work["is_persistent_cluster"] = False

        cluster_objects: List[PersistentThermalCluster] = []
        unique_labels = set(labels)

        for cid in sorted(unique_labels):
            if cid == -1:
                # Noise points (single isolated detections)
                continue

            sub_df = df_work[df_work["cluster_id"] == cid]
            lats = sub_df["latitude"].tolist()
            lons = sub_df["longitude"].tolist()

            cent_lat, cent_lon = calculate_cluster_centroid(lats, lons)

            # Spatial spread radius
            max_dist_m = 0.0
            for lat, lon in zip(lats, lons):
                d = haversine_distance(cent_lat, cent_lon, lat, lon, unit="meters")
                if d > max_dist_m:
                    max_dist_m = d

            # Temporal calculations
            if "acq_datetime" in sub_df.columns:
                dt_series = pd.to_datetime(sub_df["acq_datetime"], errors="coerce").dropna()
            elif "acq_date" in sub_df.columns:
                dt_series = pd.to_datetime(sub_df["acq_date"], errors="coerce").dropna()
            else:
                dt_series = pd.Series([pd.Timestamp.now()])

            if not dt_series.empty:
                first_seen = str(dt_series.min())
                last_seen = str(dt_series.max())
                time_span = (dt_series.max() - dt_series.min()).total_seconds() / 86400.0
                unique_dates = len(dt_series.dt.date.unique())
            else:
                first_seen = "UNKNOWN"
                last_seen = "UNKNOWN"
                time_span = 0.0
                unique_dates = 1

            # FRP and Brightness metrics
            if "frp" in sub_df.columns:
                frp_vals = pd.to_numeric(sub_df["frp"], errors="coerce").fillna(0.0)
            else:
                frp_vals = pd.Series(0.0, index=sub_df.index)
            mean_frp = float(frp_vals.mean())
            max_frp = float(frp_vals.max())

            if "brightness_primary" in sub_df.columns:
                bright_prim = pd.to_numeric(sub_df["brightness_primary"], errors="coerce").fillna(300.0)
            elif "bright_ti4" in sub_df.columns:
                bright_prim = pd.to_numeric(sub_df["bright_ti4"], errors="coerce").fillna(300.0)
            else:
                bright_prim = pd.Series(300.0, index=sub_df.index)
            mean_bright = float(bright_prim.mean())

            if "confidence_score" in sub_df.columns:
                conf_vals = pd.to_numeric(sub_df["confidence_score"], errors="coerce").fillna(50.0)
            elif "confidence" in sub_df.columns:
                conf_vals = pd.to_numeric(sub_df["confidence"], errors="coerce").fillna(50.0)
            else:
                conf_vals = pd.Series(50.0, index=sub_df.index)
            mean_conf = float(conf_vals.mean())

            # Night observation ratio
            if "daynight" in sub_df.columns:
                night_obs = (sub_df["daynight"].astype(str).str.upper() == "N").sum()
                night_ratio = float(night_obs / len(sub_df))
            else:
                night_ratio = 0.0

            obs_count = len(sub_df)
            is_persist = (
                (obs_count >= self.min_persistence_observations and (time_span >= self.min_duration_days or unique_dates >= 2))
                or (obs_count >= 3)
            )

            df_work.loc[df_work["cluster_id"] == cid, "is_persistent_cluster"] = is_persist

            cluster_obj = PersistentThermalCluster(
                cluster_id=int(cid),
                centroid_lat=cent_lat,
                centroid_lon=cent_lon,
                observation_count=obs_count,
                first_seen=first_seen,
                last_seen=last_seen,
                duration_days=time_span,
                mean_frp=mean_frp,
                max_frp=max_frp,
                mean_brightness=mean_bright,
                mean_confidence=mean_conf,
                night_ratio=night_ratio,
                spatial_radius_m=max_dist_m,
                is_persistent=is_persist,
                records=sub_df.to_dict(orient="records"),
            )
            cluster_objects.append(cluster_obj)

        self.clusters_ = cluster_objects
        return df_work, cluster_objects

    def enrich_dataframe_with_persistence(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Runs clustering and adds 'persistence_count' and 'persistence_days' directly onto observations.
        """
        if df.empty:
            df["persistence_count"] = []
            df["persistence_days"] = []
            df["cluster_id"] = []
            return df

        df_clustered, clusters = self.fit_predict_clusters(df)

        cluster_map = {c.cluster_id: c for c in clusters}

        persist_counts = []
        persist_days = []

        for cid in df_clustered["cluster_id"]:
            if cid in cluster_map:
                c = cluster_map[cid]
                persist_counts.append(c.observation_count)
                persist_days.append(c.duration_days)
            else:
                persist_counts.append(1)
                persist_days.append(0.0)

        df_clustered["persistence_count"] = persist_counts
        df_clustered["persistence_days"] = persist_days

        return df_clustered

    def train(self, train_data: Any, val_data: Any = None) -> Dict[str, Any]:
        """Cluster training data to identify baseline persistent thermal patterns."""
        if isinstance(train_data, pd.DataFrame):
            _, clusters = self.fit_predict_clusters(train_data)
            return {
                "clusters_found": len(clusters),
                "persistent_sources": len([c for c in clusters if c.is_persistent]),
            }
        return {"status": "unsupported_data_type"}

    def predict(self, input_data: Any) -> Any:
        """Assign input observations to nearest discovered persistent clusters or detect new clusters."""
        if isinstance(input_data, pd.DataFrame):
            df_out, _ = self.fit_predict_clusters(input_data)
            return df_out["is_persistent_cluster"].values
        elif isinstance(input_data, dict):
            lat = float(input_data.get("latitude", 0.0))
            lon = float(input_data.get("longitude", 0.0))
            # Match against known persistent clusters
            for c in self.clusters_:
                if c.is_persistent:
                    dist = haversine_distance(lat, lon, c.centroid_lat, c.centroid_lon, unit="meters")
                    if dist <= self.spatial_eps_meters:
                        return {"is_persistent": True, "cluster": c.to_dict(), "distance_m": dist}
            return {"is_persistent": False, "distance_m": None}
        return False

    def evaluate(self, test_data: Any) -> Dict[str, Any]:
        """Compute clustering performance statistics."""
        if isinstance(test_data, pd.DataFrame):
            df_out, clusters = self.fit_predict_clusters(test_data)
            total_points = len(test_data)
            noise_points = (df_out["cluster_id"] == -1).sum()
            clustered_points = total_points - noise_points
            persistent_clusters = [c for c in clusters if c.is_persistent]

            return {
                "total_observations": total_points,
                "clustered_observations": int(clustered_points),
                "noise_observations": int(noise_points),
                "noise_ratio": float(noise_points / max(1, total_points)),
                "total_clusters": len(clusters),
                "persistent_clusters_count": len(persistent_clusters),
            }
        return {}

    def save(self, path: Union[str, Path]) -> None:
        """Save discovered persistent clusters to JSON file."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "spatial_eps_meters": self.spatial_eps_meters,
            "min_samples": self.min_samples,
            "min_persistence_observations": self.min_persistence_observations,
            "min_duration_days": self.min_duration_days,
            "clusters": [c.to_dict() for c in self.clusters_],
        }
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"ThermalDetector clusters saved to {p}")

    def load(self, path: Union[str, Path]) -> None:
        """Load persistent clusters from JSON file."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Cluster checkpoint not found at: {p}")
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.spatial_eps_meters = data.get("spatial_eps_meters", self.spatial_eps_meters)
        self.min_samples = data.get("min_samples", self.min_samples)
        self.min_persistence_observations = data.get("min_persistence_observations", self.min_persistence_observations)
        self.min_duration_days = data.get("min_duration_days", self.min_duration_days)

        self.clusters_ = [
            PersistentThermalCluster(
                cluster_id=c["cluster_id"],
                centroid_lat=c["centroid_latitude"],
                centroid_lon=c["centroid_longitude"],
                observation_count=c["observation_count"],
                first_seen=c["first_seen_utc"],
                last_seen=c["last_seen_utc"],
                duration_days=c["persistence_duration_days"],
                mean_frp=c["mean_frp_mw"],
                max_frp=c["max_frp_mw"],
                mean_brightness=c["mean_brightness_kelvin"],
                mean_confidence=c["mean_confidence"],
                night_ratio=c["night_observation_ratio"],
                spatial_radius_m=c["spatial_radius_meters"],
                is_persistent=c["is_persistent"],
            )
            for c in data.get("clusters", [])
        ]
        logger.info(f"Loaded {len(self.clusters_)} clusters from {p}")
