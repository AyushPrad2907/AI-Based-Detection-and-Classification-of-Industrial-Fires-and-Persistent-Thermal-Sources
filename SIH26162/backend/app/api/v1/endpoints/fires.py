"""
SIH26162 — Fire Detection & ML Classification Endpoints.

Provides endpoints for real-time model inference, batch classification,
database queries for satellite observations and classifications,
and explainable multi-factor risk scores.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

from app.api.v1.schemas.fires import (
    BatchClassificationRequest,
    BatchClassificationResponse,
    ClassificationRecordItem,
    FIRMSObservationItem,
    FireClassificationRequest,
    FireClassificationResponse,
    ModelStatusResponse,
    PaginatedClassificationsResponse,
    PaginatedObservationsResponse,
)
from app.core.database import get_db
from app.repositories.firms_repository import FIRMSObservationRepository
from app.repositories.classification_repository import ClassificationRepository
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
        "phase": "Phase 3 (PostgreSQL + PostGIS Persistence & CRUD)",
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
            "query_observations": "GET /api/v1/fires/observations",
            "query_classifications": "GET /api/v1/fires/classifications",
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
async def classify_detection(
    payload: FireClassificationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Classifies a thermal anomaly using real ML model inference,
    queries OpenStreetMap for industrial infrastructure context,
    and returns an explainable multi-factor risk score.
    Optionally persists the result if payload.persist is True.
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

        # Optional persistence
        classification_id = None
        if payload.persist and db is not None:
            try:
                clf_repo = ClassificationRepository(db)
                rb = result.get("risk_breakdown", {})
                clf_record = await clf_repo.create_classification_with_risk(
                    classification_data={
                        "latitude": payload.latitude,
                        "longitude": payload.longitude,
                        "predicted_class": result["predicted_class"],
                        "confidence": result["classification_confidence"],
                        "class_probabilities": result["class_probabilities"],
                        "model_version": "random_forest_v1",
                    },
                    risk_data={
                        "risk_score": result["risk_score"],
                        "risk_level": result["risk_level"],
                        "frp_subscore": rb.get("frp_subscore", 0.0),
                        "industrial_proximity_subscore": rb.get("industrial_proximity_subscore", 0.0),
                        "persistence_subscore": rb.get("persistence_subscore", 0.0),
                        "confidence_subscore": rb.get("confidence_subscore", 0.0),
                        "nocturnal_subscore": rb.get("nocturnal_subscore", 0.0),
                        "reasons": result.get("reasons", []),
                    },
                )
                classification_id = clf_record.id
            except Exception as e:
                logger.warning(f"Could not persist classification to DB: {e}")

        result["classification_id"] = classification_id
        return FireClassificationResponse(**result)

    except RuntimeError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(err),
        )
    except Exception as err:
        logger.error(f"Error during fire classification: {err}", exc_info=True)
        detail_msg = "Classification inference error: An internal error occurred." if settings.environment != "development" else f"Classification inference error: {str(err)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail_msg,
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
        detail_msg = "Batch classification error: An internal error occurred." if settings.environment != "development" else f"Batch classification error: {str(err)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail_msg,
        )


@router.get(
    "/observations",
    response_model=PaginatedObservationsResponse,
    summary="Query ingested FIRMS observations with spatial, temporal, and sensor filters",
)
async def query_firms_observations(
    start_date: Optional[datetime] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (YYYY-MM-DD)"),
    satellite: Optional[str] = Query(None, description="Satellite sensor filter (e.g. VIIRS_SNPP_NRT)"),
    instrument: Optional[str] = Query(None, description="Instrument filter (VIIRS/MODIS)"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum confidence score"),
    min_frp: Optional[float] = Query(None, ge=0.0, description="Minimum Fire Radiative Power (MW)"),
    max_frp: Optional[float] = Query(None, ge=0.0, description="Maximum Fire Radiative Power (MW)"),
    bbox_str: Optional[str] = Query(None, alias="bbox", description="Bounding box: min_lon,min_lat,max_lon,max_lat"),
    cluster_id: Optional[int] = Query(None, description="Filter by assigned spatial cluster ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Paginated database query for satellite active fire observations with spatial bounding box
    and spectral attribute filtering.
    """
    bbox = None
    if isinstance(bbox_str, str) and bbox_str.strip():
        coords = [float(x.strip()) for x in bbox_str.split(",")]
        if len(coords) == 4:
            bbox = (coords[0], coords[1], coords[2], coords[3])

    if db is None:
        return PaginatedObservationsResponse(
            total=0,
            page=page,
            limit=limit,
            total_pages=1,
            observations=[],
        )

    offset = (page - 1) * limit
    repo = FIRMSObservationRepository(db)
    records, total_count = await repo.query_observations(
        start_date=start_date,
        end_date=end_date,
        satellite=satellite,
        instrument=instrument,
        min_confidence=min_confidence,
        min_frp=min_frp,
        max_frp=max_frp,
        bbox=bbox,
        cluster_id=cluster_id,
        limit=limit,
        offset=offset,
    )

    total_pages = max(1, (total_count + limit - 1) // limit)
    items = [
        FIRMSObservationItem(
            id=r.id,
            latitude=r.latitude,
            longitude=r.longitude,
            brightness_primary=r.brightness_primary,
            brightness_secondary=r.brightness_secondary,
            frp=r.frp,
            confidence_score=r.confidence_score,
            confidence_category=r.confidence_category,
            acq_datetime=r.acq_datetime,
            satellite=r.satellite,
            instrument=r.instrument,
            daynight=r.daynight,
            scan=r.scan,
            track=r.track,
            cluster_id=r.cluster_id,
        )
        for r in records
    ]

    return PaginatedObservationsResponse(
        total=total_count,
        page=page,
        limit=limit,
        total_pages=total_pages,
        observations=items,
    )


@router.get(
    "/classifications",
    response_model=PaginatedClassificationsResponse,
    summary="Query stored ML classification records and risk assessments",
)
async def query_stored_classifications(
    predicted_class: Optional[str] = Query(None, description="Filter by predicted class"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum classification probability"),
    risk_level: Optional[str] = Query(None, description="Filter by risk tier (LOW, MODERATE, HIGH, CRITICAL)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Paginated database query for persisted ML classifications and linked risk assessments.
    """
    if db is None:
        return PaginatedClassificationsResponse(
            total=0,
            page=page,
            limit=limit,
            total_pages=1,
            classifications=[],
        )

    offset = (page - 1) * limit
    repo = ClassificationRepository(db)
    records, total_count = await repo.query_classifications(
        predicted_class=predicted_class,
        min_confidence=min_confidence,
        risk_level=risk_level,
        limit=limit,
        offset=offset,
    )

    total_pages = max(1, (total_count + limit - 1) // limit)
    items = [
        ClassificationRecordItem(
            id=r.id,
            observation_id=r.observation_id,
            latitude=r.latitude,
            longitude=r.longitude,
            predicted_class=r.predicted_class,
            confidence=r.confidence,
            class_probabilities=r.class_probabilities,
            model_version=r.model_version,
            risk_score=r.risk_assessment.risk_score if r.risk_assessment else None,
            risk_level=r.risk_assessment.risk_level if r.risk_assessment else None,
            reasons=r.risk_assessment.reasons if r.risk_assessment else None,
            created_at=r.created_at,
        )
        for r in records
    ]

    return PaginatedClassificationsResponse(
        total=total_count,
        page=page,
        limit=limit,
        total_pages=total_pages,
        classifications=items,
    )


@router.get("/{fire_id}", summary="Get specific fire detection record")
async def get_fire(
    fire_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details for a specific fire record ID from database."""
    if db is None:
        return {
            "fire_id": fire_id,
            "status": "placeholder",
            "description": f"Fire detection record #{fire_id}",
        }

    repo = FIRMSObservationRepository(db)
    record = await repo.get_by_id(fire_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Observation #{fire_id} not found in database.")

    return {
        "id": record.id,
        "latitude": record.latitude,
        "longitude": record.longitude,
        "brightness_primary": record.brightness_primary,
        "brightness_secondary": record.brightness_secondary,
        "frp": record.frp,
        "confidence_score": record.confidence_score,
        "acq_datetime": record.acq_datetime.isoformat() if record.acq_datetime else None,
        "satellite": record.satellite,
        "instrument": record.instrument,
        "cluster_id": record.cluster_id,
    }
