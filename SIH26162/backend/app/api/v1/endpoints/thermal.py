"""
SIH26162 — Persistent Thermal Source Endpoints.

Provides endpoints to query spatial-temporal clusters, persistent industrial thermal anomalies,
and multi-pass satellite telemetry with database CRUD support.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.thermal import (
    PersistentThermalClusterResponse,
    ThermalSourcesQueryResponse,
)
from app.core.database import get_db
from app.repositories.thermal_source_repository import ThermalSourceRepository
from ml.models.thermal_detector import ThermalDetector
from ml.utils.data_utils import FIRMSDatasetLoader

logger = logging.getLogger(__name__)

router = APIRouter()

detector = ThermalDetector()
data_loader = FIRMSDatasetLoader()


@router.get("/", summary="Persistent thermal sources summary")
async def list_sources():
    """Summary of persistent thermal source tracking capabilities."""
    return {
        "service": "SIH26162 Persistent Thermal Source Detector",
        "phase": "Phase 3 (PostgreSQL + PostGIS Persistence & CRUD)",
        "status": "placeholder",
        "algorithm": "Spatio-Temporal DBSCAN with Haversine Great-Circle Metric",
        "endpoints": {
            "get_persistent_sources": "GET /api/v1/thermal/sources",
            "get_all_clusters": "GET /api/v1/thermal/clusters",
        },
    }


@router.get(
    "/sources",
    response_model=ThermalSourcesQueryResponse,
    summary="Query discovered persistent industrial thermal sources",
)
async def get_persistent_sources(
    min_observations: int = Query(2, ge=1, description="Minimum satellite passes to qualify"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum confidence filter"),
    persistent_only: bool = Query(True, description="Filter only clusters flagged as persistent"),
    min_frp: Optional[float] = Query(None, ge=0.0, description="Minimum mean FRP (MW)"),
    bbox_str: Optional[str] = Query(None, alias="bbox", description="Bounding box: min_lon,min_lat,max_lon,max_lat"),
    limit: int = Query(200, ge=1, le=1000, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset results"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves persistent thermal sources identified via spatio-temporal clustering.
    Queries the PostGIS database if populated, or runs live clustering across FIRMS datasets as fallback.
    """
    try:
        bbox = None
        if isinstance(bbox_str, str) and bbox_str.strip():
            coords = [float(x.strip()) for x in bbox_str.split(",")]
            if len(coords) == 4:
                bbox = (coords[0], coords[1], coords[2], coords[3])

        # 1. Try querying from database repository first
        if db is not None:
            try:
                repo = ThermalSourceRepository(db)
                db_sources, total_db = await repo.query_sources(
                    persistent_only=persistent_only,
                    min_observations=min_observations,
                    min_frp=min_frp,
                    bbox=bbox,
                    limit=limit,
                    offset=offset,
                )
                if total_db > 0:
                    cluster_responses = [
                        PersistentThermalClusterResponse(
                            cluster_id=s.cluster_id,
                            centroid_latitude=s.centroid_lat,
                            centroid_longitude=s.centroid_lon,
                            observation_count=s.observation_count,
                            first_seen_utc=s.first_seen_utc.isoformat() if s.first_seen_utc else "",
                            last_seen_utc=s.last_seen_utc.isoformat() if s.last_seen_utc else "",
                            persistence_duration_days=s.persistence_duration_days,
                            mean_frp_mw=s.mean_frp_mw,
                            max_frp_mw=s.max_frp_mw,
                            mean_brightness_kelvin=s.mean_brightness_kelvin,
                            mean_confidence=s.mean_confidence,
                            night_observation_ratio=s.night_observation_ratio,
                            spatial_radius_meters=s.spatial_radius_meters,
                            is_persistent=s.is_persistent,
                        )
                        for s in db_sources
                    ]
                    return ThermalSourcesQueryResponse(
                        total_clusters=total_db,
                        persistent_sources_count=len([s for s in db_sources if s.is_persistent]),
                        clusters=cluster_responses,
                        query_parameters={
                            "source": "database",
                            "min_observations": min_observations,
                            "min_confidence": min_confidence,
                            "persistent_only": persistent_only,
                            "bbox": bbox,
                        },
                    )
            except Exception as e:
                logger.debug(f"Database query fallback to file engine: {e}")

        # 2. Fallback to dataset loader & clustering engine
        df = data_loader.load_dataset(min_confidence=min_confidence, bbox=bbox)
        if df.empty:
            return ThermalSourcesQueryResponse(
                total_clusters=0,
                persistent_sources_count=0,
                clusters=[],
                query_parameters={
                    "source": "engine",
                    "min_observations": min_observations,
                    "min_confidence": min_confidence,
                    "persistent_only": persistent_only,
                    "bbox": bbox,
                },
            )

        custom_detector = ThermalDetector(min_persistence_observations=min_observations)
        _, clusters = custom_detector.fit_predict_clusters(df)

        if persistent_only:
            filtered_clusters = [c for c in clusters if c.is_persistent]
        else:
            filtered_clusters = clusters

        if isinstance(min_frp, (int, float)):
            filtered_clusters = [c for c in filtered_clusters if c.mean_frp >= min_frp]

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
            for c in filtered_clusters[offset:offset + limit]
        ]

        return ThermalSourcesQueryResponse(
            total_clusters=len(clusters),
            persistent_sources_count=len([c for c in clusters if c.is_persistent]),
            clusters=cluster_responses,
            query_parameters={
                "source": "engine",
                "min_observations": min_observations,
                "min_confidence": min_confidence if isinstance(min_confidence, (int, float)) else None,
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
async def get_all_clusters(
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all discovered thermal clusters without persistence filtering."""
    return await get_persistent_sources(
        min_observations=1,
        min_confidence=None,
        persistent_only=False,
        min_frp=None,
        bbox_str=None,
        limit=500,
        offset=0,
        db=db,
    )
