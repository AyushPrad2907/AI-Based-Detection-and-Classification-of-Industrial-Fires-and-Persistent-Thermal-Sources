"""
SIH26162 — Geospatial & OSM Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IndustrialFacilitySchema(BaseModel):
    """Schema representing a nearby industrial facility mapped in OSM."""
    osm_id: Optional[int] = None
    osm_type: Optional[str] = None
    name: str
    facility_type: str
    latitude: float
    longitude: float
    distance_meters: float
    tags: Dict[str, Any] = {}


class IndustrialContextRequest(BaseModel):
    """Request schema for querying industrial context around coordinates."""
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    radius_m: int = Field(5000, ge=500, le=25000, description="Search radius in meters")


class IndustrialContextResponse(BaseModel):
    """Response schema for industrial context."""
    is_industrial_nearby: bool
    min_distance_m: float
    min_distance_km: float
    nearest_facility_name: Optional[str] = None
    nearest_facility_type: Optional[str] = None
    total_facilities_in_radius: int
    facilities: List[IndustrialFacilitySchema] = []
    query_latitude: float
    query_longitude: float
    search_radius_m: int
    status: str


class IndustrialFacilityRecord(BaseModel):
    """Schema representing an industrial facility stored in PostGIS."""
    id: int
    osm_id: Optional[int] = None
    osm_type: Optional[str] = None
    name: str
    facility_type: str
    latitude: float
    longitude: float
    tags: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class SeedFacilitiesResponse(BaseModel):
    """Response schema for industrial facility seeding."""
    status: str
    message: str
    total_seeded: int
    categories: Dict[str, int] = {}

