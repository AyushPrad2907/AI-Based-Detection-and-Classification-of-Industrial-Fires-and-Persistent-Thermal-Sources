"""
SIH26162 — Real ML Inference Pipeline.

Orchestrates live inference on thermal anomaly observations using trained
classifier models, geospatial features, and explainable risk scoring.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from ml.inference.risk_scorer import RiskScorer
from ml.models.fire_classifier import FireClassifier
from ml.preprocessing.feature_builder import FeatureBuilder

logger = logging.getLogger(__name__)


class Predictor:
    """
    Production inference engine for real-time thermal anomaly classification and risk scoring.
    """

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        default_model_path: Union[str, Path] = "ml/saved_models/fire_classifier.joblib",
    ):
        self.model_path = Path(model_path) if model_path else Path(default_model_path)
        self.classifier: Optional[FireClassifier] = None
        self.feature_builder = FeatureBuilder()
        self.risk_scorer = RiskScorer()
        self._load_if_available()

    def _load_if_available(self) -> bool:
        """Attempt to load model from disk if checkpoint exists."""
        if self.model_path.exists() and self.model_path.is_file():
            try:
                clf = FireClassifier()
                clf.load(self.model_path)
                self.classifier = clf
                self.feature_builder = FeatureBuilder(feature_columns=clf.feature_columns)
                logger.info(f"Loaded trained FireClassifier from: {self.model_path}")
                return True
            except Exception as err:
                logger.error(f"Error loading model from {self.model_path}: {err}")
                return False
        return False

    def load_model(self, model_path: Optional[Union[str, Path]] = None) -> None:
        """Explicitly load or reload model checkpoint."""
        if model_path:
            self.model_path = Path(model_path)
        if not self._load_if_available():
            raise FileNotFoundError(f"Trained model artifact not found at: {self.model_path}")

    def predict(
        self,
        record: Dict[str, Any],
        osm_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute full end-to-end inference on a single observation.

        Args:
            record: Dictionary with observation fields (latitude, longitude, frp, brightness_primary, etc.)
            osm_context: Optional OpenStreetMap industrial context.

        Returns:
            Dictionary containing prediction class, probabilities, risk score, and explainable reasons.
        """
        if self.classifier is None or not self.classifier.is_fitted:
            self._load_if_available()

        if self.classifier is None or not self.classifier.is_fitted:
            raise RuntimeError(
                "Classification model is not loaded. Train a model first via `ml.training.trainer`."
            )

        # 1. ML Classification
        clf_result = self.classifier.predict_single(record, osm_context=osm_context)

        # 2. Risk Scoring & Explainability
        frp = float(record.get("frp", 0.0) or 0.0)
        conf = float(record.get("confidence_score", record.get("confidence", 50.0)) or 50.0)

        dist_ind_m = None
        facility_name = None
        facility_type = None

        if osm_context:
            dist_ind_m = osm_context.get("min_distance_m")
            facility_name = osm_context.get("nearest_facility_name")
            facility_type = osm_context.get("nearest_facility_type")
        elif "dist_to_industrial_km" in record:
            dist_ind_m = float(record["dist_to_industrial_km"]) * 1000.0

        persist_count = int(record.get("persistence_count", 1) or 1)
        persist_days = float(record.get("persistence_days", 0.0) or 0.0)

        daynight = str(record.get("daynight", "D")).upper()
        is_night = daynight == "N" or float(record.get("is_night", 0.0) or 0.0) >= 0.5

        risk_result = self.risk_scorer.calculate_risk(
            frp=frp,
            confidence=conf,
            dist_to_industrial_m=dist_ind_m,
            facility_name=facility_name,
            facility_type=facility_type,
            persistence_count=persist_count,
            persistence_days=persist_days,
            is_night=is_night,
        )

        return {
            "predicted_class": clf_result["predicted_class"],
            "confidence": clf_result["confidence"],
            "class_probabilities": clf_result["class_probabilities"],
            "risk_score": risk_result["risk_score"],
            "risk_level": risk_result["risk_level"],
            "risk_breakdown": risk_result["breakdown"],
            "reasons": risk_result["reasons"],
            "features_used": self.classifier.feature_columns,
        }

    def batch_predict(
        self,
        records: List[Dict[str, Any]],
        osm_contexts: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute inference on a list of thermal observations.
        """
        results: List[Dict[str, Any]] = []
        for i, rec in enumerate(records):
            ctx = osm_contexts[i] if osm_contexts and i < len(osm_contexts) else None
            res = self.predict(rec, osm_context=ctx)
            results.append(res)
        return results
