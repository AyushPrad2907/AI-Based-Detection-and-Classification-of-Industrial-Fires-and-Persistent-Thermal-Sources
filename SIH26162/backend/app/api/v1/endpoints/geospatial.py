"""
SIH26162 — Geospatial and OpenStreetMap Context Endpoints.

Provides endpoints for spatial analysis, OpenStreetMap industrial facility querying,
and geographic proximity lookups.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.geospatial import (
    IndustrialContextRequest,
    IndustrialContextResponse,
    IndustrialFacilitySchema,
    IndustrialFacilityRecord,
    SeedFacilitiesResponse,
)
from app.core.database import get_db
from app.repositories.facility_repository import IndustrialFacilityRepository
from app.services.facility_seeder import seed_industrial_facilities
from app.services.osm_service import OSMService

logger = logging.getLogger(__name__)

router = APIRouter()
osm_service = OSMService()


@router.get("/", summary="Geospatial service overview")
async def list_geospatial_data():
    """Summary of geospatial context and OSM integration capabilities."""
    return {
        "service": "SIH26162 Geospatial Analytics & OpenStreetMap Context",
        "status": "active",
        "features": [
            "Industrial infrastructure proximity querying",
            "PostGIS 127 Strategic Indian Industrial Assets Gazetteer",
            "Power plants, refineries, chemical works, and foundries detection",
            "Spatial caching and rate-limiting protection",
        ],
        "endpoints": {
            "industrial_context": "POST /api/v1/geospatial/industrial-context",
            "facilities": "GET /api/v1/geospatial/facilities",
            "seed_facilities": "POST /api/v1/geospatial/seed-facilities",
        },
    }


@router.post(
    "/seed-facilities",
    response_model=SeedFacilitiesResponse,
    summary="Seed 127 strategic Indian industrial facilities into PostGIS",
    status_code=status.HTTP_200_OK,
)
async def seed_facilities_endpoint(
    db: AsyncSession = Depends(get_db),
):
    """
    Seeds curated strategic Indian industrial facilities (refineries, steel plants,
    thermal power plants, petrochemical zones) from data/industrial_facilities_india.json
    into the PostGIS industrial_facilities table.
    """
    res = await seed_industrial_facilities(db)
    if res.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=res.get("message", "Seeding failed"),
        )
    return SeedFacilitiesResponse(**res)


@router.get(
    "/facilities",
    response_model=List[IndustrialFacilityRecord],
    summary="List industrial facilities stored in PostGIS",
    status_code=status.HTTP_200_OK,
)
async def list_facilities_endpoint(
    facility_type: Optional[str] = Query(None, description="Filter by facility type (e.g., refinery, power_plant, steel_mill)"),
    limit: int = Query(200, ge=1, le=1000, description="Max facilities to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve indexed strategic industrial facilities from the PostGIS database.
    """
    try:
        repo = IndustrialFacilityRepository(db)
        facilities = await repo.list_facilities(facility_type=facility_type, limit=limit, offset=offset)
        return [
            IndustrialFacilityRecord(
                id=f.id,
                osm_id=f.osm_id,
                osm_type=f.osm_type,
                name=f.name,
                facility_type=f.facility_type,
                latitude=f.latitude,
                longitude=f.longitude,
                tags=f.tags or {},
            )
            for f in facilities
        ]
    except Exception as err:
        logger.error(f"Error listing facilities: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch industrial facilities: {str(err)}",
        )



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
