"""
SIH26162 — Fire Detection & ML Classification Endpoints.

Provides endpoints for real-time model inference, batch classification,
model operational status, and explainable risk scores.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.api.v1.schemas.fires import (
    BatchClassificationRequest,
    BatchClassificationResponse,
    FireClassificationRequest,
    FireClassificationResponse,
    ModelStatusResponse,
)
from app.services.classification_service import ClassificationService

logger = logging.getLogger(__name__)

router = APIRouter()

# Singleton service instance
classification_service = ClassificationService()


@router.get("/", summary="Fire detection and classification overview")
async def list_fires():
    """Summary of active fire classification and detection capabilities."""
    model_ready = classification_service.is_model_ready()
    return {
        "service": "SIH26162 Fire Classification & Thermal AI Detector",
        "phase": "Phase 2 (AI/ML & Feature Engineering)",
        "status": "placeholder",
        "model_ready": model_ready,
        "supported_classes": [
            "persistent_industrial",
            "industrial_fire",
            "wildfire",
            "agricultural_burn",
            "uncertain_anomaly",
        ],
        "endpoints": {
            "model_status": "GET /api/v1/fires/status",
            "single_classify": "POST /api/v1/fires/classify",
            "batch_classify": "POST /api/v1/fires/classify/batch",
        },
    }


@router.get("/status", response_model=ModelStatusResponse, summary="Get ML model status and metadata")
async def get_model_status():
    """Returns the operational status, loaded features, and metadata of the classifier model."""
    meta = classification_service.get_model_metadata()
    return ModelStatusResponse(
        ready=meta.get("ready", False),
        model_type=meta.get("model_type"),
        classes=meta.get("classes", []),
        features_count=meta.get("features_count", 0),
        persistent_clusters_known=meta.get("persistent_clusters_known", 0),
        model_path=meta.get("model_path", ""),
        message=meta.get("message"),
    )


@router.post(
    "/classify",
    response_model=FireClassificationResponse,
    summary="Classify a single thermal detection",
    status_code=status.HTTP_200_OK,
)
async def classify_detection(payload: FireClassificationRequest):
    """
    Classifies a thermal anomaly using real ML model inference,
    queries OpenStreetMap for industrial infrastructure context,
    and returns an explainable multi-factor risk score.
    """
    try:
        result = await classification_service.classify_thermal_source(
            latitude=payload.latitude,
            longitude=payload.longitude,
            brightness_primary=payload.brightness_primary,
            brightness_secondary=payload.brightness_secondary,
            frp=payload.frp,
            confidence=payload.confidence,
            daynight=payload.daynight,
            acq_datetime=payload.acq_datetime,
            satellite=payload.satellite,
            instrument=payload.instrument,
            query_osm=payload.query_osm,
            osm_radius_m=payload.osm_radius_m,
        )
        return FireClassificationResponse(**result)

    except RuntimeError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(err),
        )
    except Exception as err:
        logger.error(f"Error during fire classification: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification inference error: {str(err)}",
        )


@router.post(
    "/classify/batch",
    response_model=BatchClassificationResponse,
    summary="Classify multiple thermal detections in batch",
    status_code=status.HTTP_200_OK,
)
async def batch_classify_detections(payload: BatchClassificationRequest):
    """
    Classifies an array of thermal anomaly observations efficiently.
    """
    try:
        obs_dicts = [req.model_dump() for req in payload.observations]
        results = await classification_service.batch_classify(
            observations=obs_dicts,
            query_osm=payload.query_osm,
        )
        response_items = [FireClassificationResponse(**r) for r in results]
        return BatchClassificationResponse(
            total_processed=len(response_items),
            results=response_items,
        )
    except Exception as err:
        logger.error(f"Error during batch classification: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch classification error: {str(err)}",
        )


@router.get("/{fire_id}", summary="Get specific fire detection record")
async def get_fire(fire_id: int):
    """Retrieve details for a specific fire record ID."""
    return {
        "fire_id": fire_id,
        "status": "active",
        "description": f"Fire detection record #{fire_id}",
    }
