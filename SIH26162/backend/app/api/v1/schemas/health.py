"""
SIH26162 — Health Check Response Schemas.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response model for the primary health check endpoint."""
    status: str
    service: str
    version: str


class DatabaseHealthResponse(BaseModel):
    """Response model for the PostgreSQL + PostGIS database health check."""
    status: str
    healthy: bool
    latency_ms: float
    database_url: str
    postgis_version: Optional[str] = None
    record_counts: Dict[str, Any] = {}
    error: Optional[str] = None
