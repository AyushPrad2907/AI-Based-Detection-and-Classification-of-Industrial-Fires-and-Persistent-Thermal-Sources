"""
SIH26162 — Persistent Thermal Source Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PersistentThermalClusterResponse(BaseModel):
    """Schema for a persistent thermal anomaly cluster."""
    cluster_id: int
    centroid_latitude: float
    centroid_longitude: float
    observation_count: int
    first_seen_utc: str
    last_seen_utc: str
    persistence_duration_days: float
    mean_frp_mw: float
    max_frp_mw: float
    mean_brightness_kelvin: float
    mean_confidence: float
    night_observation_ratio: float
    spatial_radius_meters: float
    is_persistent: bool


class ThermalSourcesQueryResponse(BaseModel):
    """Schema for persistent thermal sources query response."""
    total_clusters: int
    persistent_sources_count: int
    clusters: List[PersistentThermalClusterResponse]
    query_parameters: Dict[str, Any]
