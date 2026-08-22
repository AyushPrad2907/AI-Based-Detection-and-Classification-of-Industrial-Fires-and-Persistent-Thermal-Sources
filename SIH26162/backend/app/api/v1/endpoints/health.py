"""
SIH26162 — Health Check Endpoint.

Provides a simple health check to verify the API is running.
"""

from fastapi import APIRouter

from app.api.v1.schemas.health import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Return the current health status of the API."""
    return HealthResponse(
        status="healthy",
        service="SIH26162 API",
        version="0.1.0",
    )
