"""
SIH26162 — NASA FIRMS Data Preprocessor.

Production-grade preprocessing pipeline for raw NASA FIRMS active fire
observations (VIIRS, MODIS, and LANDSAT).

Features:
- Schema validation against expected column contracts
- Robust coordinate range and integrity checks
- UTC timestamp synthesis (combining acq_date and 4-digit acq_time)
- Instrument standardization (harmonizing VIIRS bright_ti4/bright_ti5 and MODIS brightness/bright_t31)
- Confidence normalization (categorical 'l'/'n'/'h' <-> numeric 0-100 scale)
- Exact spatial-temporal deduplication
- Bounding box and confidence threshold filtering
- Preservation of original raw sensor fields
- Deterministic ordering and export
"""

import io
import logging
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Required core columns present in any valid FIRMS dataset
REQUIRED_CORE_COLUMNS = ["latitude", "longitude", "acq_date", "acq_time"]

# Mapping for VIIRS categorical confidence to numerical score (0-100)
VIIRS_CONFIDENCE_MAP = {
    "l": 30.0,
    "low": 30.0,
    "n": 70.0,
    "nominal": 70.0,
    "h": 100.0,
    "high": 100.0,
}


class PreprocessingValidationError(Exception):
    """Raised when FIRMS dataset fails validation checks."""
    pass


class FIRMSPreprocessor:
    """
    Cleans, validates, normalizes, and filters raw NASA FIRMS fire datasets.
    """

    def __init__(
        self,
        min_confidence: Optional[Union[str, float, int]] = None,
        bbox: Optional[Sequence[Union[int, float]]] = None,
    ):
        """
        Initialize the preprocessor.

        Args:
            min_confidence: Optional filter ('low', 'nominal', 'high' or numeric 0-100).
            bbox: Optional bounding box filter (min_lon, min_lat, max_lon, max_lat).
        """
        self.min_confidence = min_confidence
        self.bbox = bbox

    def load_raw_data(self, source: Union[str, Path, io.StringIO, pd.DataFrame]) -> pd.DataFrame:
        """
        Load raw FIRMS data from a file path, raw string buffer, or existing DataFrame.
        """
        if isinstance(source, pd.DataFrame):
            df = source.copy()
        elif isinstance(source, (str, Path)):
            p = Path(source)
            if p.exists() and p.is_file():
                df = pd.read_csv(p)
            elif isinstance(source, str) and ("\n" in source or "," in source):
                # String content
                df = pd.read_csv(io.StringIO(source))
            else:
                raise FileNotFoundError(f"FIRMS data file not found at: {source}")
        elif isinstance(source, io.StringIO):
            df = pd.read_csv(source)
        else:
            raise ValueError(f"Unsupported data source type: {type(source)}")

        if df.empty:
            logger.warning("Loaded empty FIRMS dataset.")
            return df

        # Standardize column headers: lowercase and strip whitespace
        df.columns = [str(col).strip().lower() for col in df.columns]
        return df

    def validate_schema(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate that all required core columns exist in the DataFrame.
        """
        if df.empty:
            return True, []

        missing_cols = [col for col in REQUIRED_CORE_COLUMNS if col not in df.columns]
        if missing_cols:
            return False, missing_cols
        return True, []

    def validate_and_clean_coordinates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate latitude and longitude ranges.
        Latitude must be within [-90.0, 90.0].
        Longitude must be within [-180.0, 180.0].
        Drops invalid or non-numeric coordinates.
        """
        if df.empty:
            return df

        df = df.copy()
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

        initial_len = len(df)
        valid_mask = (
            df["latitude"].notna()
            & df["longitude"].notna()
            & (df["latitude"] >= -90.0)
            & (df["latitude"] <= 90.0)
            & (df["longitude"] >= -180.0)
            & (df["longitude"] <= 180.0)
        )
        cleaned_df = df[valid_mask].copy()

        dropped = initial_len - len(cleaned_df)
        if dropped > 0:
            logger.warning(f"Dropped {dropped} observations with invalid or missing coordinates.")

        return cleaned_df

    def parse_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Combine acq_date and acq_time into a timezone-naive UTC acq_datetime column.
        FIRMS acq_time is represented as UTC integer/string (e.g., 430 -> 04:30:00, 1430 -> 14:30:00).
        """
        if df.empty:
            return df

        df = df.copy()

        def _format_acq_time(val: Any) -> str:
            if pd.isna(val) or val == "":
                return "0000"
            try:
                # Handle floats like 430.0 or ints like 430
                clean_str = str(int(float(val))).strip()
            except (ValueError, TypeError):
                clean_str = str(val).strip().replace(":", "")
            return clean_str.zfill(4)[:4]

        formatted_time = df["acq_time"].apply(_format_acq_time)
        datetime_str = df["acq_date"].astype(str).str.strip() + " " + formatted_time

        df["acq_datetime"] = pd.to_datetime(
            datetime_str, format="%Y-%m-%d %H%M", errors="coerce"
        )

        # Fallback for any records where parsing with format failed
        if df["acq_datetime"].isna().any():
            fallback_mask = df["acq_datetime"].isna()
            df.loc[fallback_mask, "acq_datetime"] = pd.to_datetime(
                df.loc[fallback_mask, "acq_date"].astype(str), errors="coerce"
            )

        return df

    def normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize brightness and confidence fields across VIIRS and MODIS instruments
        while preserving all original sensor fields.
        """
        if df.empty:
            return df

        df = df.copy()

        # 1. Primary and Secondary Brightness
        if "bright_ti4" in df.columns:
            # VIIRS 375m I-4 channel brightness temp (Kelvin)
            df["brightness_primary"] = pd.to_numeric(df["bright_ti4"], errors="coerce")
        elif "brightness" in df.columns:
            # MODIS channel 21/22 brightness temp (Kelvin)
            df["brightness_primary"] = pd.to_numeric(df["brightness"], errors="coerce")
        else:
            df["brightness_primary"] = np.nan

        if "bright_ti5" in df.columns:
            # VIIRS 375m I-5 channel brightness temp (Kelvin)
            df["brightness_secondary"] = pd.to_numeric(df["bright_ti5"], errors="coerce")
        elif "bright_t31" in df.columns:
            # MODIS channel 31 brightness temp (Kelvin)
            df["brightness_secondary"] = pd.to_numeric(df["bright_t31"], errors="coerce")
        else:
            df["brightness_secondary"] = np.nan

        # 2. Fire Radiative Power (FRP in Megawatts)
        if "frp" in df.columns:
            df["frp"] = pd.to_numeric(df["frp"], errors="coerce").fillna(0.0)
            df["frp"] = df["frp"].apply(lambda x: max(0.0, float(x)))
        else:
            df["frp"] = 0.0

        # 3. Confidence Normalization
        # VIIRS uses 'l', 'n', 'h'; MODIS uses 0-100; Landsat may use categorical/numeric.
        def _normalize_confidence(val: Any) -> Tuple[float, str]:
            if pd.isna(val) or val == "":
                return 50.0, "nominal"
            str_val = str(val).strip().lower()
            if str_val in VIIRS_CONFIDENCE_MAP:
                score = VIIRS_CONFIDENCE_MAP[str_val]
                cat = "low" if score <= 30 else ("high" if score >= 80 else "nominal")
                return score, cat
            try:
                num = float(val)
                clamped_num = max(0.0, min(100.0, num))
                if clamped_num < 30.0:
                    return clamped_num, "low"
                elif clamped_num >= 80.0:
                    return clamped_num, "high"
                else:
                    return clamped_num, "nominal"
            except (ValueError, TypeError):
                return 50.0, "nominal"

        if "confidence" in df.columns:
            res = df["confidence"].apply(_normalize_confidence)
            df["confidence_score"] = res.apply(lambda x: x[0])
            df["confidence_category"] = res.apply(lambda x: x[1])
        else:
            df["confidence_score"] = 50.0
            df["confidence_category"] = "nominal"

        # 4. Standardize Satellite / Instrument / DayNight
        if "satellite" in df.columns:
            df["satellite"] = df["satellite"].astype(str).str.strip().str.upper()
        else:
            df["satellite"] = "UNKNOWN"

        if "instrument" in df.columns:
            df["instrument"] = df["instrument"].astype(str).str.strip().str.upper()
        else:
            df["instrument"] = "UNKNOWN"

        if "daynight" in df.columns:
            df["daynight"] = df["daynight"].astype(str).str.strip().str.upper()
            df["daynight"] = df["daynight"].apply(lambda x: x if x in ("D", "N") else "UNKNOWN")
        else:
            df["daynight"] = "UNKNOWN"

        return df

    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove exact duplicate fire detections based on spatial, temporal, and sensor coordinates.
        """
        if df.empty:
            return df

        df = df.copy()
        dedup_cols = ["latitude", "longitude", "acq_datetime", "satellite", "instrument"]
        available_cols = [c for c in dedup_cols if c in df.columns]

        initial_len = len(df)
        df_dedup = df.drop_duplicates(subset=available_cols, keep="first").copy()
        dropped = initial_len - len(df_dedup)

        if dropped > 0:
            logger.info(f"Removed {dropped} duplicate fire observations.")

        return df_dedup

    def filter_by_confidence(
        self,
        df: pd.DataFrame,
        min_confidence: Optional[Union[str, float, int]] = None,
    ) -> pd.DataFrame:
        """
        Filter observations by minimum confidence category or score.
        """
        threshold = min_confidence if min_confidence is not None else self.min_confidence
        if threshold is None or df.empty:
            return df

        df = df.copy()
        if isinstance(threshold, str):
            t_lower = threshold.strip().lower()
            if t_lower in ("high", "h"):
                return df[df["confidence_category"] == "high"].copy()
            elif t_lower in ("nominal", "n"):
                return df[df["confidence_category"].isin(["nominal", "high"])].copy()
            elif t_lower in ("low", "l"):
                return df
            else:
                try:
                    num_thresh = float(threshold)
                    return df[df["confidence_score"] >= num_thresh].copy()
                except ValueError:
                    logger.warning(f"Unknown confidence filter '{threshold}'. Skipping filter.")
                    return df
        elif isinstance(threshold, (int, float)):
            return df[df["confidence_score"] >= float(threshold)].copy()

        return df

    def filter_by_bbox(
        self,
        df: pd.DataFrame,
        bbox: Optional[Sequence[Union[int, float]]] = None,
    ) -> pd.DataFrame:
        """
        Filter observations within geographic bounding box: (min_lon, min_lat, max_lon, max_lat).
        """
        bb = bbox if bbox is not None else self.bbox
        if bb is None or df.empty:
            return df

        min_lon, min_lat, max_lon, max_lat = (float(x) for x in bb)
        mask = (
            (df["longitude"] >= min_lon)
            & (df["longitude"] <= max_lon)
            & (df["latitude"] >= min_lat)
            & (df["latitude"] <= max_lat)
        )
        return df[mask].copy()

    def preprocess(
        self,
        source: Union[str, Path, io.StringIO, pd.DataFrame],
        output_path: Optional[Union[str, Path]] = None,
    ) -> pd.DataFrame:
        """
        Execute the complete FIRMS preprocessing pipeline.

        Steps:
        1. Load raw data
        2. Validate required core schema
        3. Validate and clean coordinates
        4. Parse and synthesize UTC timestamps
        5. Normalize instrument columns & confidence metrics
        6. Remove duplicate observations
        7. Apply confidence and spatial bounding box filters
        8. Sort deterministically
        9. Save clean output to CSV if output_path is provided
        10. Return clean processed DataFrame
        """
        raw_df = self.load_raw_data(source)
        if raw_df.empty:
            logger.warning("Empty input data provided to FIRMS preprocessor.")
            if output_path:
                p = Path(output_path)
                p.parent.mkdir(parents=True, exist_ok=True)
                raw_df.to_csv(p, index=False)
            return raw_df

        # Step 1: Validate Schema
        is_valid, missing = self.validate_schema(raw_df)
        if not is_valid:
            raise PreprocessingValidationError(
                f"Missing required columns in FIRMS dataset: {missing}"
            )

        # Step 2: Validate Coordinates
        df = self.validate_and_clean_coordinates(raw_df)
        if df.empty:
            logger.warning("No valid observations remaining after coordinate validation.")
            return df

        # Step 3: Parse Timestamps
        df = self.parse_timestamps(df)

        # Step 4: Normalize Sensor Columns & Confidence
        df = self.normalize_columns(df)

        # Step 5: Remove Duplicates
        df = self.remove_duplicates(df)

        # Step 6: Apply Filters
        df = self.filter_by_confidence(df)
        df = self.filter_by_bbox(df)

        # Step 7: Deterministic Ordering
        sort_cols = [c for c in ["acq_datetime", "latitude", "longitude"] if c in df.columns]
        if sort_cols:
            df = df.sort_values(by=sort_cols, ascending=True).reset_index(drop=True)

        # Step 8: Save to disk if requested
        if output_path:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(out, index=False)
            logger.info(f"Processed FIRMS data successfully saved to: {out} ({len(df)} records)")

        return df
