"""
SIH26162 — Fire Detection, Classification & Observation Schemas.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class FireClassificationRequest(BaseModel):
    """Request payload for thermal anomaly classification."""
    model_config = ConfigDict(protected_namespaces=())

    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    brightness_primary: float = Field(325.0, ge=200.0, le=600.0, description="Primary brightness temperature in Kelvin")
    brightness_secondary: Optional[float] = Field(None, ge=200.0, le=600.0, description="Secondary brightness temp in Kelvin")
    frp: float = Field(15.0, ge=0.0, description="Fire Radiative Power in MW")
    confidence: float = Field(
        80.0,
        ge=0.0,
        le=100.0,
        validation_alias=AliasChoices("confidence", "confidence_score"),
        description="Detection confidence score (0-100)",
    )
    daynight: str = Field("D", description="'D' for Daytime or 'N' for Nighttime observation")
    acq_datetime: Optional[str] = Field(None, description="UTC Acquisition datetime (YYYY-MM-DD HH:MM:SS)")
    satellite: str = Field("VIIRS_SNPP_NRT", description="Satellite source name")
    instrument: str = Field("VIIRS", description="Sensor instrument")
    query_osm: bool = Field(True, description="Whether to query OpenStreetMap for industrial proximity")
    osm_radius_m: int = Field(5000, ge=500, le=25000, description="OSM search radius in meters")
    persist: bool = Field(False, description="Whether to persist classification to database")


class RiskBreakdownSchema(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    frp_subscore: float
    industrial_proximity_subscore: float
    persistence_subscore: float
    confidence_subscore: float
    nocturnal_subscore: float


class FireClassificationResponse(BaseModel):
    """Response payload for thermal anomaly classification."""
    model_config = ConfigDict(protected_namespaces=())

    latitude: float
    longitude: float
    predicted_class: str
    classification_confidence: float
    class_probabilities: Dict[str, float]
    risk_score: float
    risk_level: str
    risk_breakdown: RiskBreakdownSchema
    reasons: List[str]
    is_persistent_source: bool
    persistent_cluster: Optional[Dict[str, Any]] = None
    industrial_context: Optional[Dict[str, Any]] = None
    thermal_parameters: Dict[str, Any]
    classification_id: Optional[int] = None


class BatchClassificationRequest(BaseModel):
    """Batch classification request payload."""
    model_config = ConfigDict(protected_namespaces=())

    observations: List[FireClassificationRequest] = Field(..., min_length=1, max_length=500)
    query_osm: bool = Field(False, description="Whether to query OSM for each point in batch")
    persist: bool = Field(False, description="Whether to persist classifications to database")


class BatchClassificationResponse(BaseModel):
    """Batch classification response."""
    model_config = ConfigDict(protected_namespaces=())

    total_processed: int
    results: List[FireClassificationResponse]


class ModelStatusResponse(BaseModel):
    """ML model operational status and metadata."""
    model_config = ConfigDict(protected_namespaces=())

    ready: bool
    model_type: Optional[str] = None
    classes: List[str] = []
    features_count: int = 0
    persistent_clusters_known: int = 0
    model_path: str
    message: Optional[str] = None


class FIRMSObservationItem(BaseModel):
    """Individual FIRMS observation schema for database queries."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: Optional[int] = None
    latitude: float
    longitude: float
    brightness_primary: float
    brightness_secondary: Optional[float] = None
    frp: float
    confidence_score: float
    confidence_category: str
    acq_datetime: datetime
    satellite: str
    instrument: str
    daynight: str
    scan: float
    track: float
    cluster_id: Optional[int] = None


class PaginatedObservationsResponse(BaseModel):
    """Paginated response for FIRMS satellite observations."""
    model_config = ConfigDict(protected_namespaces=())

    total: int
    page: int
    limit: int
    total_pages: int
    observations: List[FIRMSObservationItem]


class ClassificationRecordItem(BaseModel):
    """Stored classification record schema."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    observation_id: Optional[int] = None
    latitude: float
    longitude: float
    predicted_class: str
    confidence: float
    class_probabilities: Dict[str, float]
    model_version: str
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    reasons: Optional[List[str]] = None
    created_at: datetime


class PaginatedClassificationsResponse(BaseModel):
    """Paginated response for stored classifications."""
    model_config = ConfigDict(protected_namespaces=())

    total: int
    page: int
    limit: int
    total_pages: int
    classifications: List[ClassificationRecordItem]
