"""
SIH26162 — Thermal Source Endpoints (Placeholder).

These endpoints will handle persistent thermal source monitoring,
classification, and historical analysis.

NOT YET IMPLEMENTED — returns placeholder responses.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_thermal_sources():
    """List persistent thermal sources. NOT YET IMPLEMENTED."""
    return {
        "message": "Thermal source endpoints — not yet implemented",
        "status": "placeholder",
        "planned_features": [
            "List persistent thermal sources",
            "Classify thermal source types (industrial, wildfire, agricultural)",
            "Historical thermal pattern analysis",
        ],
    }
