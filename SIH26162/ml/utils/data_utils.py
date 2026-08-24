"""
SIH26162 — Dataset Loader and Data Utilities.

Handles dataset loading, multi-sensor merging, temporal-spatial filtering,
and integrity validation for real NASA FIRMS observations and enriched datasets.
"""

import glob
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
import pandas as pd

from ml.utils.geo_utils import point_in_bbox

logger = logging.getLogger(__name__)


def load_csv(filepath: Union[str, Path]) -> pd.DataFrame:
    """
    Load a single CSV file into a pandas DataFrame with normalized column names.

    Args:
        filepath: Path to the CSV file.

    Returns:
        DataFrame with standardized lowercase stripped column headers.
    """
    p = Path(filepath)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"File not found: {filepath}")

    df = pd.read_csv(p)
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


class FIRMSDatasetLoader:
    """
    Production dataset loader for multi-file, multi-sensor, multi-date NASA FIRMS data.
    """

    def __init__(
        self,
        data_dir: Optional[Union[str, Path]] = None,
        default_processed_dir: Union[str, Path] = "data/processed/firms",
    ):
        self.data_dir = Path(data_dir) if data_dir is not None else Path(default_processed_dir)

    def discover_files(
        self,
        pattern: str = "*processed*.csv",
        directory: Optional[Union[str, Path]] = None,
    ) -> List[Path]:
        """
        Discover all matching FIRMS CSV files in the target directory.

        Args:
            pattern: Glob pattern to match files.
            directory: Directory to search (defaults to self.data_dir).

        Returns:
            Sorted list of resolved Path objects.
        """
        search_dir = Path(directory) if directory is not None else self.data_dir
        if not search_dir.exists():
            logger.warning(f"Data directory does not exist: {search_dir}")
            return []

        matched = sorted(search_dir.glob(pattern))
        if not matched:
            # Fallback to general *.csv if pattern had no match
            matched = sorted(search_dir.glob("*.csv"))
        return [p.resolve() for p in matched]

    def load_dataset(
        self,
        sources: Optional[Union[str, Path, Sequence[Union[str, Path]]]] = None,
        sensors: Optional[Sequence[str]] = None,
        bbox: Optional[Sequence[Union[int, float]]] = None,
        min_confidence: Optional[float] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        deduplicate: bool = True,
    ) -> pd.DataFrame:
        """
        Load, merge, validate, and standardize multiple FIRMS data files.

        Args:
            sources: Single file path, directory path, or list of file paths.
                     If None, discovers all processed CSVs in self.data_dir.
            sensors: Optional filter by satellite/sensor (e.g. ['VIIRS', 'MODIS', 'VIIRS_SNPP_NRT']).
            bbox: Optional geographic bounding box (min_lon, min_lat, max_lon, max_lat).
            min_confidence: Optional minimum confidence threshold (0-100).
            start_date: Optional ISO start date (YYYY-MM-DD).
            end_date: Optional ISO end date (YYYY-MM-DD).
            deduplicate: Whether to remove duplicate observations across overlapping query files.

        Returns:
            Consolidated, clean pandas DataFrame.
        """
        file_paths: List[Path] = []

        if sources is None:
            file_paths = self.discover_files()
        elif isinstance(sources, (str, Path)):
            p = Path(sources)
            if p.is_dir():
                file_paths = sorted(p.glob("*.csv"))
            elif p.is_file():
                file_paths = [p]
            else:
                # Might be a glob string
                file_paths = [Path(f) for f in sorted(glob.glob(str(sources)))]
        else:
            for s in sources:
                sp = Path(s)
                if sp.is_file():
                    file_paths.append(sp)
                elif sp.is_dir():
                    file_paths.extend(sorted(sp.glob("*.csv")))

        if not file_paths:
            logger.warning("No FIRMS CSV files found to load.")
            return pd.DataFrame()

        dfs: List[pd.DataFrame] = []
        for path in file_paths:
            try:
                sub_df = pd.read_csv(path)
                sub_df.columns = [str(c).strip().lower() for c in sub_df.columns]
                if not sub_df.empty:
                    sub_df["_source_file"] = path.name
                    dfs.append(sub_df)
            except Exception as err:
                logger.error(f"Error loading FIRMS file '{path}': {err}")

        if not dfs:
            return pd.DataFrame()

        merged_df = pd.concat(dfs, ignore_index=True)

        # Standardize core column types
        merged_df = self._standardize_schema(merged_df)

        # Remove duplicate observations across merged files
        if deduplicate and not merged_df.empty:
            initial_len = len(merged_df)
            dedup_cols = ["latitude", "longitude", "acq_datetime", "satellite", "instrument"]
            avail_cols = [c for c in dedup_cols if c in merged_df.columns]
            if avail_cols:
                merged_df = merged_df.drop_duplicates(subset=avail_cols, keep="first").reset_index(drop=True)
                logger.info(f"Deduplication: {initial_len} -> {len(merged_df)} observations.")

        # Apply Filters
        if bbox is not None and not merged_df.empty:
            min_lon, min_lat, max_lon, max_lat = (float(x) for x in bbox)
            merged_df = merged_df[
                (merged_df["longitude"] >= min_lon)
                & (merged_df["longitude"] <= max_lon)
                & (merged_df["latitude"] >= min_lat)
                & (merged_df["latitude"] <= max_lat)
            ].reset_index(drop=True)

        if min_confidence is not None and not merged_df.empty and "confidence_score" in merged_df.columns:
            merged_df = merged_df[merged_df["confidence_score"] >= float(min_confidence)].reset_index(drop=True)

        if start_date is not None and not merged_df.empty and "acq_datetime" in merged_df.columns:
            merged_df = merged_df[merged_df["acq_datetime"] >= pd.to_datetime(start_date)].reset_index(drop=True)

        if end_date is not None and not merged_df.empty and "acq_datetime" in merged_df.columns:
            merged_df = merged_df[merged_df["acq_datetime"] <= pd.to_datetime(end_date + " 23:59:59")].reset_index(drop=True)

        if sensors is not None and not merged_df.empty:
            sensors_upper = [s.strip().upper() for s in sensors]
            mask = False
            if "instrument" in merged_df.columns:
                mask = mask | merged_df["instrument"].astype(str).str.upper().isin(sensors_upper)
            if "satellite" in merged_df.columns:
                mask = mask | merged_df["satellite"].astype(str).str.upper().isin(sensors_upper)
            merged_df = merged_df[mask].reset_index(drop=True)

        # Deterministic sorting
        sort_cols = [c for c in ["acq_datetime", "latitude", "longitude"] if c in merged_df.columns]
        if sort_cols and not merged_df.empty:
            merged_df = merged_df.sort_values(by=sort_cols, ascending=True).reset_index(drop=True)

        logger.info(f"Loaded {len(merged_df)} validated FIRMS records from {len(file_paths)} file(s).")
        return merged_df

    def _standardize_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure consistent datatypes and derived fields."""
        df = df.copy()

        # Coordinates
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
        df = df.dropna(subset=["latitude", "longitude"])

        # Timestamp synthesis if acq_datetime is missing
        if "acq_datetime" not in df.columns or df["acq_datetime"].isna().any():
            if "acq_date" in df.columns:
                if "acq_time" in df.columns:
                    def _fmt_time(t):
                        if pd.isna(t) or t == "":
                            return "0000"
                        try:
                            return str(int(float(t))).strip().zfill(4)[:4]
                        except Exception:
                            return str(t).strip().replace(":", "").zfill(4)[:4]
                    formatted_time = df["acq_time"].apply(_fmt_time)
                    dt_str = df["acq_date"].astype(str) + " " + formatted_time
                    df["acq_datetime"] = pd.to_datetime(dt_str, format="%Y-%m-%d %H%M", errors="coerce")
                else:
                    df["acq_datetime"] = pd.to_datetime(df["acq_date"], errors="coerce")

        if "acq_datetime" in df.columns:
            df["acq_datetime"] = pd.to_datetime(df["acq_datetime"], errors="coerce")

        # Thermal fields
        if "brightness_primary" not in df.columns:
            if "bright_ti4" in df.columns:
                df["brightness_primary"] = pd.to_numeric(df["bright_ti4"], errors="coerce")
            elif "brightness" in df.columns:
                df["brightness_primary"] = pd.to_numeric(df["brightness"], errors="coerce")
            else:
                df["brightness_primary"] = np.nan

        if "brightness_secondary" not in df.columns:
            if "bright_ti5" in df.columns:
                df["brightness_secondary"] = pd.to_numeric(df["bright_ti5"], errors="coerce")
            elif "bright_t31" in df.columns:
                df["brightness_secondary"] = pd.to_numeric(df["bright_t31"], errors="coerce")
            else:
                df["brightness_secondary"] = np.nan

        if "frp" not in df.columns:
            df["frp"] = 0.0
        else:
            df["frp"] = pd.to_numeric(df["frp"], errors="coerce").fillna(0.0).clip(lower=0.0)

        # Confidence
        if "confidence_score" not in df.columns:
            if "confidence" in df.columns:
                def _conf_score(c):
                    if pd.isna(c) or c == "":
                        return 50.0
                    c_str = str(c).strip().lower()
                    if c_str in ("l", "low"):
                        return 30.0
                    if c_str in ("n", "nominal"):
                        return 70.0
                    if c_str in ("h", "high"):
                        return 100.0
                    try:
                        return max(0.0, min(100.0, float(c)))
                    except Exception:
                        return 50.0
                df["confidence_score"] = df["confidence"].apply(_conf_score)
            else:
                df["confidence_score"] = 50.0

        if "confidence_category" not in df.columns:
            df["confidence_category"] = df["confidence_score"].apply(
                lambda s: "low" if s < 40 else ("high" if s >= 80 else "nominal")
            )

        if "daynight" in df.columns:
            df["daynight"] = df["daynight"].astype(str).str.strip().str.upper()
            df["daynight"] = df["daynight"].apply(lambda x: x if x in ("D", "N") else "UNKNOWN")
        else:
            df["daynight"] = "UNKNOWN"

        return df

    def get_dataset_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate statistical summary of a loaded FIRMS dataset.
        """
        if df.empty:
            return {"count": 0, "status": "empty"}

        summary = {
            "total_observations": int(len(df)),
            "latitude_range": (float(df["latitude"].min()), float(df["latitude"].max())),
            "longitude_range": (float(df["longitude"].min()), float(df["longitude"].max())),
            "mean_frp": float(df["frp"].mean()) if "frp" in df.columns else 0.0,
            "max_frp": float(df["frp"].max()) if "frp" in df.columns else 0.0,
            "mean_brightness_primary": float(df["brightness_primary"].mean()) if "brightness_primary" in df.columns else 0.0,
            "mean_confidence": float(df["confidence_score"].mean()) if "confidence_score" in df.columns else 0.0,
        }

        if "acq_datetime" in df.columns and df["acq_datetime"].notna().any():
            summary["date_min"] = str(df["acq_datetime"].min())
            summary["date_max"] = str(df["acq_datetime"].max())

        if "instrument" in df.columns:
            summary["instruments"] = df["instrument"].value_counts().to_dict()

        if "satellite" in df.columns:
            summary["satellites"] = df["satellite"].value_counts().to_dict()

        if "daynight" in df.columns:
            summary["daynight_distribution"] = df["daynight"].value_counts().to_dict()

        return summary
