"""
SIH26162 — Fire and Thermal Anomaly Classification Service.

Orchestrates real machine learning inference, OpenStreetMap industrial proximity enrichment,
and explainable risk scoring for incoming thermal anomaly observations.

Zero hardcoding: all predictions are produced by trained scikit-learn models.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from app.services.osm_service import OSMService
from ml.inference.predictor import Predictor
from ml.inference.risk_scorer import RiskScorer
from ml.models.fire_classifier import FireClassifier
from ml.models.thermal_detector import ThermalDetector

logger = logging.getLogger(__name__)


class ClassificationService:
    """
    Production service orchestrating ML classification, OSM context, and risk scoring.
    """

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        clusters_path: Optional[Union[str, Path]] = None,
        osm_service: Optional[OSMService] = None,
    ):
        self.model_path = Path(model_path) if model_path else Path("ml/saved_models/fire_classifier.joblib")
        self.clusters_path = Path(clusters_path) if clusters_path else Path("ml/saved_models/persistent_clusters.json")
        self.osm_service = osm_service or OSMService()
        self.predictor = Predictor(model_path=self.model_path)
        self.thermal_detector = ThermalDetector()
        self.risk_scorer = RiskScorer()
        self._load_clusters_if_available()

    def _load_clusters_if_available(self) -> None:
        """Load persistent clusters if file exists."""
        if self.clusters_path.exists() and self.clusters_path.is_file():
            try:
                self.thermal_detector.load(self.clusters_path)
                logger.info(f"ClassificationService loaded {len(self.thermal_detector.clusters_)} persistent clusters.")
            except Exception as err:
                logger.warning(f"Could not load persistent clusters ({err}).")

    def is_model_ready(self) -> bool:
        """Check whether the ML classifier is fitted and ready for inference."""
        return self.predictor.classifier is not None and self.predictor.classifier.is_fitted

    def get_model_metadata(self) -> Dict[str, Any]:
        """Return model metadata, feature names, classes, and readiness."""
        if not self.is_model_ready():
            return {
                "ready": False,
                "model_path": str(self.model_path),
                "message": "Model not loaded. Train a model first via `scripts/train_model.py`.",
            }

        clf = self.predictor.classifier
        return {
            "ready": True,
            "model_type": clf.model_type,
            "classes": [str(c) for c in clf.class_labels],
            "feature_columns": clf.feature_columns,
            "features_count": len(clf.feature_columns),
            "persistent_clusters_known": len(self.thermal_detector.clusters_),
            "model_path": str(self.model_path),
        }

    async def classify_thermal_source(
        self,
        latitude: float,
        longitude: float,
        brightness_primary: float = 325.0,
        brightness_secondary: Optional[float] = None,
        frp: float = 15.0,
        confidence: float = 80.0,
        daynight: str = "D",
        acq_datetime: Optional[str] = None,
        scan: float = 0.375,
        track: float = 0.375,
        satellite: str = "VIIRS_SNPP_NRT",
        instrument: str = "VIIRS",
        query_osm: bool = True,
        osm_radius_m: int = 5000,
    ) -> Dict[str, Any]:
        """
        Classify a single thermal detection with full ML inference, OSM context, and risk scoring.

        Args:
            latitude: Observation latitude.
            longitude: Observation longitude.
            brightness_primary: Primary channel brightness temp in Kelvin.
            brightness_secondary: Secondary channel brightness temp in Kelvin.
            frp: Fire Radiative Power in MW.
            confidence: Satellite confidence (0-100).
            daynight: 'D' (Day) or 'N' (Night).
            acq_datetime: ISO UTC acquisition datetime.
            scan: Pixel scan size.
            track: Pixel track size.
            satellite: Satellite name.
            instrument: Sensor instrument.
            query_osm: Whether to fetch OpenStreetMap industrial infrastructure context.
            osm_radius_m: Search radius in meters for OSM querying.

        Returns:
            Complete prediction response dictionary.
        """
        if not self.is_model_ready():
            self.predictor._load_if_available()
            if not self.is_model_ready():
                raise RuntimeError(
                    "Classification model artifact is missing. "
                    "Please run `python scripts/train_model.py` to train and save the model."
                )

        # 1. Fetch OSM Context if requested
        osm_context = None
        if query_osm:
            try:
                osm_context = await self.osm_service.get_industrial_context(
                    latitude=latitude,
                    longitude=longitude,
                    radius_m=osm_radius_m,
                )
            except Exception as err:
                logger.warning(f"OSM context fetch error ({err}). Proceeding without OSM.")
                osm_context = None

        # 2. Check persistence against known clusters
        persist_match = self.thermal_detector.predict({"latitude": latitude, "longitude": longitude})
        is_persist = persist_match.get("is_persistent", False) if isinstance(persist_match, dict) else False
        cluster_info = persist_match.get("cluster") if isinstance(persist_match, dict) else None

        persist_count = cluster_info.get("observation_count", 1) if cluster_info else 1
        persist_days = cluster_info.get("persistence_duration_days", 0.0) if cluster_info else 0.0

        # 3. Assemble record for ML Predictor
        bright_sec = brightness_secondary if brightness_secondary is not None else (brightness_primary - 25.0)

        record = {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "brightness_primary": float(brightness_primary),
            "brightness_secondary": float(bright_sec),
            "frp": float(frp),
            "confidence_score": float(confidence),
            "daynight": str(daynight).upper(),
            "acq_datetime": acq_datetime or "2026-08-24 12:00:00",
            "scan": float(scan),
            "track": float(track),
            "satellite": str(satellite),
            "instrument": str(instrument),
            "persistence_count": persist_count,
            "persistence_days": persist_days,
            "dist_to_industrial_km": (osm_context["min_distance_km"] if osm_context else 10.0),
        }

        # 4. Run ML Inference & Risk Scoring
        inference_res = self.predictor.predict(record=record, osm_context=osm_context)

        return {
            "latitude": latitude,
            "longitude": longitude,
            "predicted_class": inference_res["predicted_class"],
            "classification_confidence": inference_res["confidence"],
            "class_probabilities": inference_res["class_probabilities"],
            "risk_score": inference_res["risk_score"],
            "risk_level": inference_res["risk_level"],
            "risk_breakdown": inference_res["risk_breakdown"],
            "reasons": inference_res["reasons"],
            "is_persistent_source": is_persist,
            "persistent_cluster": cluster_info,
            "industrial_context": osm_context,
            "thermal_parameters": {
                "frp_mw": frp,
                "brightness_primary_k": brightness_primary,
                "brightness_secondary_k": bright_sec,
                "confidence_score": confidence,
                "daynight": daynight,
            },
        }

    async def batch_classify(
        self,
        observations: List[Dict[str, Any]],
        query_osm: bool = False,
        max_concurrency: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Classify multiple thermal observations efficiently using bounded concurrency.

        Args:
            observations: List of observation dictionaries.
            query_osm: Whether to query OSM for each observation.
            max_concurrency: Maximum number of concurrent classifications (limits OSM API load).

        Returns:
            List of classification result dictionaries in the same order as input.
        """
        semaphore = asyncio.Semaphore(max_concurrency)

        async def _classify_one(obs: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                bright_prim = float(obs.get("brightness_primary") or obs.get("bright_ti4") or 325.0)
                bright_sec = float(obs.get("brightness_secondary") or obs.get("bright_ti5") or (bright_prim - 25.0))
                frp_val = float(obs.get("frp") if obs.get("frp") is not None else 15.0)
                conf_val = float(obs.get("confidence") or obs.get("confidence_score") or 80.0)
                scan_val = float(obs.get("scan") if obs.get("scan") is not None else 0.375)
                track_val = float(obs.get("track") if obs.get("track") is not None else 0.375)

                return await self.classify_thermal_source(
                    latitude=float(obs["latitude"]),
                    longitude=float(obs["longitude"]),
                    brightness_primary=bright_prim,
                    brightness_secondary=bright_sec,
                    frp=frp_val,
                    confidence=conf_val,
                    daynight=str(obs.get("daynight") or "D"),
                    acq_datetime=obs.get("acq_datetime"),
                    scan=scan_val,
                    track=track_val,
                    satellite=str(obs.get("satellite") or "VIIRS"),
                    instrument=str(obs.get("instrument") or "VIIRS"),
                    query_osm=query_osm,
                )

        results = await asyncio.gather(*[_classify_one(obs) for obs in observations])
        return list(results)

