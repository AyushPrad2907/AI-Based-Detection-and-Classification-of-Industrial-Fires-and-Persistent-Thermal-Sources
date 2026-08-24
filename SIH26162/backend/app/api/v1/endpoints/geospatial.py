"""
SIH26162 — Geospatial and OpenStreetMap Context Endpoints.

Provides endpoints for spatial analysis, OpenStreetMap industrial facility querying,
and geographic proximity lookups.
"""

import logging
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Query, status

from app.api.v1.schemas.geospatial import (
    IndustrialContextRequest,
    IndustrialContextResponse,
    IndustrialFacilitySchema,
)
from app.services.osm_service import OSMService

logger = logging.getLogger(__name__)

router = APIRouter()
osm_service = OSMService()


@router.get("/", summary="Geospatial service overview")
async def list_geospatial_data():
    """Summary of geospatial context and OSM integration capabilities."""
    return {
        "service": "SIH26162 Geospatial Analytics & OpenStreetMap Context",
        "status": "placeholder",
        "features": [
            "Industrial infrastructure proximity querying",
            "Power plants, refineries, chemical works, and foundries detection",
            "Spatial caching and rate-limiting protection",
        ],
        "endpoints": {
            "industrial_context": "POST /api/v1/geospatial/industrial-context",
        },
    }


@router.post(
    "/industrial-context",
    response_model=IndustrialContextResponse,
    summary="Query OpenStreetMap industrial facilities around a location",
    status_code=status.HTTP_200_OK,
)
async def query_industrial_context(payload: IndustrialContextRequest):
    """
    Queries OpenStreetMap (Overpass API) to discover industrial infrastructure,
    power generation, and manufacturing facilities within the specified radius.
    """
    try:
        res = await osm_service.get_industrial_context(
            latitude=payload.latitude,
            longitude=payload.longitude,
            radius_m=payload.radius_m,
        )

        facility_schemas = [
            IndustrialFacilitySchema(
                osm_id=f.get("osm_id"),
                osm_type=f.get("osm_type"),
                name=f.get("name", "Unnamed Facility"),
                facility_type=f.get("facility_type", "industrial"),
                latitude=f.get("latitude", payload.latitude),
                longitude=f.get("longitude", payload.longitude),
                distance_meters=f.get("distance_meters", 0.0),
                tags=f.get("tags", {}),
            )
            for f in res.get("facilities", [])
        ]

        return IndustrialContextResponse(
            is_industrial_nearby=res.get("is_industrial_nearby", False),
            min_distance_m=res.get("min_distance_m", float(payload.radius_m)),
            min_distance_km=res.get("min_distance_km", float(payload.radius_m) / 1000.0),
            nearest_facility_name=res.get("nearest_facility_name"),
            nearest_facility_type=res.get("nearest_facility_type"),
            total_facilities_in_radius=res.get("total_facilities_in_radius", 0),
            facilities=facility_schemas,
            query_latitude=res.get("query_latitude", payload.latitude),
            query_longitude=res.get("query_longitude", payload.longitude),
            search_radius_m=res.get("search_radius_m", payload.radius_m),
            status=res.get("status", "success"),
        )
    except Exception as err:
        logger.error(f"Error querying industrial context: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Industrial context query failed: {str(err)}",
        )
