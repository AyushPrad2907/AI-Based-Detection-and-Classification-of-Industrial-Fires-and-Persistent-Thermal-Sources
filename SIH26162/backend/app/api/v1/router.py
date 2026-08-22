"""
SIH26162 — API v1 Router.

Aggregates all v1 endpoint routers into a single router
that is included by the main application.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, fires, thermal, geospatial

api_v1_router = APIRouter()

# Include sub-routers
api_v1_router.include_router(health.router, prefix="/health", tags=["Health"])
api_v1_router.include_router(fires.router, prefix="/fires", tags=["Fire Detection"])
api_v1_router.include_router(thermal.router, prefix="/thermal", tags=["Thermal Sources"])
api_v1_router.include_router(geospatial.router, prefix="/geospatial", tags=["Geospatial"])
