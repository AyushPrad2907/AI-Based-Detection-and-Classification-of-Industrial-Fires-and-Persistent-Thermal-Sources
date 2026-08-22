"""
SIH26162 — Geospatial Data Endpoints (Placeholder).

These endpoints will handle geospatial queries, map tile serving,
and spatial analysis of fire/thermal data.

NOT YET IMPLEMENTED — returns placeholder responses.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_geospatial_data():
    """List geospatial datasets. NOT YET IMPLEMENTED."""
    return {
        "message": "Geospatial data endpoints — not yet implemented",
        "status": "placeholder",
        "planned_features": [
            "Query fire data by geographic bounding box",
            "OpenStreetMap land-use overlay",
            "Spatial clustering of thermal hotspots",
        ],
    }
