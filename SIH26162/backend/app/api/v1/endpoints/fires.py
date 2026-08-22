"""
SIH26162 — Fire Detection Endpoints (Placeholder).

These endpoints will handle fire detection queries, active fire data
retrieval, and fire classification results.

NOT YET IMPLEMENTED — returns placeholder responses.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_fires():
    """List detected fires. NOT YET IMPLEMENTED."""
    return {
        "message": "Fire detection endpoints — not yet implemented",
        "status": "placeholder",
        "planned_features": [
            "List active fire detections",
            "Filter by region, date, severity",
            "Get fire classification details",
        ],
    }


@router.get("/{fire_id}")
async def get_fire(fire_id: int):
    """Get details of a specific fire detection. NOT YET IMPLEMENTED."""
    return {
        "message": f"Fire detection {fire_id} — not yet implemented",
        "status": "placeholder",
    }
