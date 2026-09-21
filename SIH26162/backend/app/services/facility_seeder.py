"""
SIH26162 — Industrial Facilities Seeder Service.

Provides automatic and on-demand seeding of the 127 curated Indian strategic
industrial installations (refineries, steel plants, thermal power stations,
chemical plants, nuclear stations, and fertilizer complexes) into PostGIS.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.facility_repository import IndustrialFacilityRepository

logger = logging.getLogger("facility_seeder")

# Path to the curated dataset
DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "industrial_facilities_india.json"


async def seed_industrial_facilities(
    session: AsyncSession,
    json_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Ingest curated Indian industrial facilities into the PostGIS industrial_facilities table.

    Returns:
        Dict with total_seeded, category_breakdown, and status.
    """
    file_to_load = json_path or DATA_PATH
    if not file_to_load.exists():
        logger.error(f"Facility dataset not found at {file_to_load}")
        return {
            "status": "error",
            "message": f"Facility file not found at {file_to_load}",
            "total_seeded": 0,
            "categories": {},
        }

    try:
        with open(file_to_load, "r", encoding="utf-8") as f:
            facilities: List[Dict[str, Any]] = json.load(f)

        # Ensure unique osm_id for upserting
        categories: Dict[str, int] = {}
        for idx, fac in enumerate(facilities, start=10001):
            if "osm_id" not in fac or fac["osm_id"] is None:
                fac["osm_id"] = idx
            ft = fac.get("facility_type", "industrial")
            categories[ft] = categories.get(ft, 0) + 1

        repo = IndustrialFacilityRepository(session)
        count = await repo.bulk_upsert_facilities(facilities)
        await session.commit()

        logger.info(f"Successfully seeded {count} industrial facilities into PostGIS database.")
        return {
            "status": "success",
            "message": f"Successfully seeded {count} industrial facilities into PostGIS.",
            "total_seeded": count,
            "categories": categories,
        }
    except Exception as exc:
        await session.rollback()
        logger.error(f"Facility seeding failed: {exc}", exc_info=True)
        return {
            "status": "error",
            "message": f"Seeding failed: {str(exc)}",
            "total_seeded": 0,
            "categories": {},
        }
