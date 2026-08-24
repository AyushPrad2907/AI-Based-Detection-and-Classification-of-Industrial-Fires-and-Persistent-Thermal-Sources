"""
SIH26162 — Persistent Thermal Source Endpoints.

Provides endpoints to discover, analyze, and monitor persistent industrial heat sources
(smelters, flaring units, refineries, foundries, power plants) using spatio-temporal clustering.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.api.v1.schemas.thermal import (
    PersistentThermalClusterResponse,
    ThermalSourcesQueryResponse,
)
from ml.models.thermal_detector import ThermalDetector
from ml.utils.data_utils import FIRMSDatasetLoader

logger = logging.getLogger(__name__)

router = APIRouter()

# Data loader and clustering detector
data_loader = FIRMSDatasetLoader()
detector = ThermalDetector()


@router.get("/", summary="Persistent thermal sources overview")
async def list_thermal_sources():
    """Summary of persistent thermal source monitoring capabilities."""
    return {
        "service": "SIH26162 Persistent Thermal Source AI Detector",
        "status": "placeholder",
        "clustering_algorithm": "DBSCAN (Haversine Metric) with Spatio-Temporal Windowing",
        "parameters": {
            "spatial_eps_meters": detector.spatial_eps_meters,
            "min_samples": detector.min_samples,
            "min_persistence_observations": detector.min_persistence_observations,
            "min_duration_days": detector.min_duration_days,
        },
        "endpoints": {
            "sources": "GET /api/v1/thermal/sources",
            "clusters": "GET /api/v1/thermal/clusters",
        },
    }


@router.get(
    "/sources",
    response_model=ThermalSourcesQueryResponse,
    summary="List persistent thermal sources from real satellite observations",
)
async def get_persistent_sources(
    min_observations: int = Query(2, ge=1, description="Minimum satellite detections to qualify as source"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum confidence filter"),
    persistent_only: bool = Query(True, description="Filter for persistent sources only"),
    bbox_str: Optional[str] = Query(None, description="Optional bbox: min_lon,min_lat,max_lon,max_lat"),
):
    """
    Runs spatial-temporal clustering across real NASA FIRMS processed observations
    and returns detected persistent industrial thermal sources with statistics.
    """
    try:
        bbox = None
        if isinstance(bbox_str, str) and bbox_str.strip():
            coords = [float(x.strip()) for x in bbox_str.split(",")]
            if len(coords) == 4:
                bbox = coords

        df = data_loader.load_dataset(min_confidence=min_confidence, bbox=bbox)
        if df.empty:
            return ThermalSourcesQueryResponse(
                total_clusters=0,
                persistent_sources_count=0,
                clusters=[],
                query_parameters={
                    "min_observations": min_observations,
                    "min_confidence": min_confidence,
                    "persistent_only": persistent_only,
                    "bbox": bbox,
                },
            )

        # Run clustering
        custom_detector = ThermalDetector(min_persistence_observations=min_observations)
        _, clusters = custom_detector.fit_predict_clusters(df)

        if persistent_only:
            filtered_clusters = [c for c in clusters if c.is_persistent]
        else:
            filtered_clusters = clusters

        cluster_responses = [
            PersistentThermalClusterResponse(
                cluster_id=c.cluster_id,
                centroid_latitude=c.centroid_lat,
                centroid_longitude=c.centroid_lon,
                observation_count=c.observation_count,
                first_seen_utc=c.first_seen,
                last_seen_utc=c.last_seen,
                persistence_duration_days=c.duration_days,
                mean_frp_mw=c.mean_frp,
                max_frp_mw=c.max_frp,
                mean_brightness_kelvin=c.mean_brightness,
                mean_confidence=c.mean_confidence,
                night_observation_ratio=c.night_ratio,
                spatial_radius_meters=c.spatial_radius_m,
                is_persistent=c.is_persistent,
            )
            for c in filtered_clusters
        ]

        return ThermalSourcesQueryResponse(
            total_clusters=len(clusters),
            persistent_sources_count=len([c for c in clusters if c.is_persistent]),
            clusters=cluster_responses,
            query_parameters={
                "min_observations": min_observations,
                "min_confidence": min_confidence,
                "persistent_only": persistent_only,
                "bbox": bbox,
                "total_observations_analyzed": len(df),
            },
        )

    except Exception as err:
        logger.error(f"Error querying thermal sources: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing thermal sources: {str(err)}",
        )


@router.get(
    "/clusters",
    response_model=ThermalSourcesQueryResponse,
    summary="Get all spatio-temporal clusters (both persistent and transient)",
)
async def get_all_clusters():
    """Retrieve all discovered thermal clusters without persistence filtering."""
    return await get_persistent_sources(
        min_observations=1,
        min_confidence=None,
        persistent_only=False,
        bbox_str=None,
    )
