"""
SIH26162 — Health Check Endpoints.

Provides application health probes and PostgreSQL + PostGIS diagnostic checks.
"""

from fastapi import APIRouter
from app.api.v1.schemas.health import HealthResponse, DatabaseHealthResponse
from app.core.database import check_database_health

router = APIRouter()


@router.get("/", response_model=HealthResponse, summary="Service health status")
async def health_check():
    """Return the current health status of the API."""
    return HealthResponse(
        status="healthy",
        service="SIH26162 API",
        version="0.1.0",
    )


@router.get("/db", response_model=DatabaseHealthResponse, summary="Database & PostGIS health status")
async def database_health_check():
    """Return connectivity, PostGIS version, and record counts from the database."""
    health_data = await check_database_health()
    return DatabaseHealthResponse(**health_data)
