"""
SIH26162 — Explainable Risk Scoring Engine.

Computes transparent, deterministic, multi-factor risk scores (0-100)
for thermal anomalies combining satellite radiative power, industrial proximity,
spatial-temporal persistence, confidence metrics, and nocturnal signatures.

Includes human-readable and machine-actionable decision explanations.
"""

import logging
import math
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class RiskScorer:
    """
    Multi-criteria explainable risk scorer for thermal anomalies.
    """

    def __init__(
        self,
        weight_frp: float = 0.30,
        weight_proximity: float = 0.25,
        weight_persistence: float = 0.20,
        weight_confidence: float = 0.15,
        weight_night: float = 0.10,
    ):
        # Validate weights sum to 1.0
        total = weight_frp + weight_proximity + weight_persistence + weight_confidence + weight_night
        self.w_frp = weight_frp / total
        self.w_prox = weight_proximity / total
        self.w_persist = weight_persistence / total
        self.w_conf = weight_confidence / total
        self.w_night = weight_night / total

    def compute_frp_subscore(self, frp: float) -> Tuple[float, Optional[str]]:
        """Compute subscore based on Fire Radiative Power (MW)."""
        frp_val = max(0.0, float(frp or 0.0))
        # Logarithmic saturation up to 100 MW
        score = min(1.0, math.log1p(frp_val) / math.log1p(100.0))
        explanation = None
        if frp_val >= 50.0:
            explanation = f"Severe thermal radiative power ({frp_val:.1f} MW) indicates intense active combustion."
        elif frp_val >= 20.0:
            explanation = f"Substantial radiative output ({frp_val:.1f} MW) detected."
        elif frp_val >= 5.0:
            explanation = f"Moderate thermal intensity ({frp_val:.1f} MW)."
        else:
            explanation = f"Low thermal radiative energy ({frp_val:.1f} MW)."
        return round(score, 4), explanation

    def compute_proximity_subscore(
        self,
        dist_m: Optional[float],
        facility_name: Optional[str] = None,
        facility_type: Optional[str] = None,
    ) -> Tuple[float, Optional[str]]:
        """Compute subscore based on proximity to industrial facilities."""
        if dist_m is None:
            return 0.10, "No mapped industrial infrastructure identified in search perimeter."

        d = float(dist_m)
        fac_desc = f"'{facility_name or facility_type or 'Industrial Facility'}'"

        if d <= 200.0:
            score = 1.0
            explanation = f"Critical proximity: Located within {d:.0f}m of {fac_desc}."
        elif d <= 500.0:
            score = 0.85
            explanation = f"High proximity: Located {d:.0f}m from {fac_desc}."
        elif d <= 1500.0:
            score = 0.60
            explanation = f"Moderate proximity: Located {d / 1000.0:.2f}km from {fac_desc}."
        elif d <= 3000.0:
            score = 0.30
            explanation = f"Low proximity: Located {d / 1000.0:.2f}km from nearest industrial zone ({fac_desc})."
        else:
            score = 0.05
            explanation = f"Distant from mapped industrial facilities (>{d / 1000.0:.1f}km)."

        return round(score, 4), explanation

    def compute_persistence_subscore(
        self,
        obs_count: int,
        duration_days: float,
    ) -> Tuple[float, Optional[str]]:
        """Compute subscore based on spatio-temporal persistence."""
        count = max(1, int(obs_count or 1))
        days = max(0.0, float(duration_days or 0.0))

        if count >= 4 or days >= 2.0:
            score = 0.95
            explanation = f"Highly persistent hotspot: Detected {count} times across {days:.1f} days."
        elif count >= 2 or days >= 0.5:
            score = 0.65
            explanation = f"Recurrent thermal activity: Detected {count} times across {days:.1f} days."
        else:
            score = 0.15
            explanation = "Single transient observation (no multi-pass persistence established)."

        return round(score, 4), explanation

    def compute_confidence_subscore(self, confidence: float) -> Tuple[float, Optional[str]]:
        """Compute subscore based on satellite detection confidence."""
        conf_val = max(0.0, min(100.0, float(confidence or 50.0)))
        score = conf_val / 100.0
        if conf_val >= 80.0:
            explanation = f"High satellite detection confidence ({conf_val:.0f}%)."
        elif conf_val >= 50.0:
            explanation = f"Nominal satellite detection confidence ({conf_val:.0f}%)."
        else:
            explanation = f"Low detection confidence ({conf_val:.0f}%)."
        return round(score, 4), explanation

    def compute_night_subscore(self, is_night: bool) -> Tuple[float, Optional[str]]:
        """Compute subscore based on nighttime observation."""
        if is_night:
            return 0.85, "Nocturnal detection confirms thermal emission independent of solar heating."
        return 0.25, "Daytime observation (subject to background solar thermal variance)."

    def calculate_risk(
        self,
        frp: float,
        confidence: float,
        dist_to_industrial_m: Optional[float] = None,
        facility_name: Optional[str] = None,
        facility_type: Optional[str] = None,
        persistence_count: int = 1,
        persistence_days: float = 0.0,
        is_night: bool = False,
    ) -> Dict[str, Any]:
        """
        Calculate total composite risk score and generate explanations.

        Returns:
            Dictionary with composite risk_score, risk_level, breakdown, and explanations list.
        """
        s_frp, exp_frp = self.compute_frp_subscore(frp)
        s_prox, exp_prox = self.compute_proximity_subscore(dist_to_industrial_m, facility_name, facility_type)
        s_persist, exp_persist = self.compute_persistence_subscore(persistence_count, persistence_days)
        s_conf, exp_conf = self.compute_confidence_subscore(confidence)
        s_night, exp_night = self.compute_night_subscore(is_night)

        # Weighted composite score on 0-100 scale
        composite = (
            self.w_frp * s_frp
            + self.w_prox * s_prox
            + self.w_persist * s_persist
            + self.w_conf * s_conf
            + self.w_night * s_night
        ) * 100.0

        risk_score = round(max(0.0, min(100.0, composite)), 1)

        # Risk level determination
        if risk_score >= 75.0:
            risk_level = "CRITICAL"
        elif risk_score >= 55.0:
            risk_level = "HIGH"
        elif risk_score >= 35.0:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        # Assemble explanations ordered by significance
        explanations: List[str] = []
        for exp in [exp_prox, exp_frp, exp_persist, exp_conf, exp_night]:
            if exp:
                explanations.append(exp)

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "breakdown": {
                "frp_subscore": s_frp,
                "industrial_proximity_subscore": s_prox,
                "persistence_subscore": s_persist,
                "confidence_subscore": s_conf,
                "nocturnal_subscore": s_night,
            },
            "weights": {
                "frp": self.w_frp,
                "proximity": self.w_prox,
                "persistence": self.w_persist,
                "confidence": self.w_conf,
                "night": self.w_night,
            },
            "reasons": explanations,
        }
