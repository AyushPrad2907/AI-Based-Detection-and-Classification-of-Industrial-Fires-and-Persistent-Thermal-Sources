"""
SIH26162 — Weak Supervision Labeling Engine.

Scientific Transparency Notice:
--------------------------------
Raw NASA FIRMS active fire observations do NOT include ground-truth class labels
(e.g., whether a thermal anomaly is an industrial flare, industrial structural fire,
wildfire, or agricultural burn).

This module implements a transparent, rule-based Weak Supervision / Silver Labeling
Engine based on peer-reviewed satellite thermal physics, spatio-temporal recurrence,
and geographic context.

These pseudo-labels are used strictly for baseline ML model training, benchmarking,
and prototype validation. They are NEVER represented as field-verified ground truth.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Standard target classification categories
CLASS_LABELS: List[str] = [
    "persistent_industrial",   # Industrial flares, smelters, continuous furnace emissions
    "industrial_fire",         # Acute industrial structural/chemical fire incidents
    "wildfire",                # Forest & vegetation fires (high FRP, rural, daytime)
    "agricultural_burn",       # Crop residue / agricultural seasonal burns (moderate FRP)
    "uncertain_anomaly",       # Low confidence, transient or borderline anomalies
]


class WeakSupervisionLabeler:
    """
    Generates transparent weak-supervision / silver pseudo-labels for FIRMS observations.
    """

    def __init__(
        self,
        industrial_dist_threshold_km: float = 2.0,
        high_frp_threshold_mw: float = 35.0,
        acute_fire_frp_threshold_mw: float = 50.0,
        min_persistent_observations: int = 2,
    ):
        self.industrial_dist_threshold_km = industrial_dist_threshold_km
        self.high_frp_threshold_mw = high_frp_threshold_mw
        self.acute_fire_frp_threshold_mw = acute_fire_frp_threshold_mw
        self.min_persistent_observations = min_persistent_observations

    def assign_label(
        self,
        record: Union[pd.Series, Dict[str, Any]],
    ) -> Tuple[str, float, str]:
        """
        Assign a weak label, heuristic confidence, and explanation string to a single observation.

        Returns:
            (label_name, heuristic_confidence, rule_explanation)
        """
        # Extract features
        frp = float(record.get("frp", 0.0) or 0.0)
        confidence = float(record.get("confidence_score", 50.0) or 50.0)
        bright_prim = float(record.get("brightness_primary", 320.0) or 320.0)
        bright_sec = float(record.get("brightness_secondary", 290.0) or 290.0)
        bright_diff = bright_prim - bright_sec

        dist_ind_km = float(record.get("dist_to_industrial_km", 10.0) if record.get("dist_to_industrial_km") is not None else 10.0)
        is_night = float(record.get("is_night", 0.0) or 0.0) >= 0.5
        persist_count = int(record.get("persistence_count", 1) or 1)
        persist_days = float(record.get("persistence_days", 0.0) or 0.0)

        # Rule 1: Low confidence or near-zero power
        if confidence < 35.0 or (frp <= 0.5 and bright_prim < 315.0):
            return (
                "uncertain_anomaly",
                0.65,
                "Low satellite detection confidence (<35%) or negligible radiative intensity."
            )

        # Rule 2: Persistent Industrial Source (co-located across passes or near industrial facility)
        is_near_industrial = dist_ind_km <= self.industrial_dist_threshold_km
        is_persistent = persist_count >= self.min_persistent_observations or persist_days >= 1.0

        if is_near_industrial and (is_persistent or is_night or frp < self.acute_fire_frp_threshold_mw):
            return (
                "persistent_industrial",
                0.85,
                f"Located {dist_ind_km:.2f}km from industrial site with steady recurrence ({persist_count} observations)."
            )

        if is_persistent and (is_night or bright_diff > 30.0) and frp < self.acute_fire_frp_threshold_mw:
            return (
                "persistent_industrial",
                0.80,
                f"Spatio-temporally persistent thermal hotspot observed {persist_count} times across {persist_days:.1f} days."
            )

        # Rule 3: Industrial Structural Fire (Acute high-intensity thermal burst in industrial zone)
        if is_near_industrial and frp >= self.acute_fire_frp_threshold_mw:
            return (
                "industrial_fire",
                0.88,
                f"Acute severe thermal output (FRP {frp:.1f} MW) within industrial perimeter ({dist_ind_km:.2f}km)."
            )

        # Rule 4: Wildfire / Vegetation Fire (High power, non-industrial, large spectral diff)
        if (frp >= self.high_frp_threshold_mw or bright_diff >= 35.0) and dist_ind_km > self.industrial_dist_threshold_km:
            return (
                "wildfire",
                0.82,
                f"High radiative intensity (FRP {frp:.1f} MW, diff {bright_diff:.1f}K) in open non-industrial terrain."
            )

        # Rule 5: Agricultural / Prescribed Burn (Moderate FRP in rural terrain, daytime)
        if 2.0 <= frp < self.high_frp_threshold_mw and dist_ind_km > self.industrial_dist_threshold_km:
            return (
                "agricultural_burn",
                0.75,
                f"Moderate thermal intensity (FRP {frp:.1f} MW) consistent with biomass/crop residue combustion."
            )

        # Default fallback
        return (
            "uncertain_anomaly",
            0.60,
            "Thermal characteristics do not definitively match distinct combustion profile."
        )

    def generate_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate weak supervision labels for an entire DataFrame.

        Returns:
            DataFrame with added columns: ['weak_label', 'label_confidence', 'label_reason']
        """
        if df.empty:
            df["weak_label"] = []
            df["label_confidence"] = []
            df["label_reason"] = []
            return df

        df = df.copy()
        labels: List[str] = []
        confs: List[float] = []
        reasons: List[str] = []

        for _, row in df.iterrows():
            lbl, cnf, rsn = self.assign_label(row)
            labels.append(lbl)
            confs.append(cnf)
            reasons.append(rsn)

        df["weak_label"] = labels
        df["label_confidence"] = confs
        df["label_reason"] = reasons

        logger.info(f"Generated weak supervision labels for {len(df)} records. Class counts:")
        for k, v in pd.Series(labels).value_counts().items():
            logger.info(f"  {k}: {v}")

        return df
