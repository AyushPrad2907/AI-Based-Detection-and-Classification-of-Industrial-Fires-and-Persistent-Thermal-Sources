"""
SIH26162 — Industrial Facilities Database Seeder.

Loads the curated 127 strategic Indian industrial facilities from
data/industrial_facilities_india.json into the PostGIS industrial_facilities table.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.core.database import async_session, init_db, check_database_health
from app.repositories.facility_repository import IndustrialFacilityRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("seed_facilities")


async def seed_facilities(json_path: Path = REPO_ROOT / "data" / "industrial_facilities_india.json"):
    print("=" * 75)
    print("SIH26162 — 127 Strategic Indian Industrial Facilities PostGIS Seeder")
    print("=" * 75)

    if not json_path.exists():
        print(f"[!] Error: Facilities file not found at {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        facilities = json.load(f)

    print(f"[*] Loaded {len(facilities)} facility records from {json_path.name}.")

    try:
        await init_db()
    except Exception as e:
        print(f"[!] Warning: init_db notice: {e}")

    # Assign synthetic unique osm_id if missing to support upsert
    for idx, fac in enumerate(facilities, start=10001):
        if "osm_id" not in fac or fac["osm_id"] is None:
            fac["osm_id"] = idx

    async with async_session() as session:
        repo = IndustrialFacilityRepository(session)
        print(f"[*] Ingesting facilities into PostGIS 'industrial_facilities' table...")
        count = await repo.bulk_upsert_facilities(facilities)
        await session.commit()
        print(f"[✓] Successfully staged and committed {count} industrial facilities into PostGIS!")

    # Verify health
    health = await check_database_health()
    print("\n" + "=" * 75)
    print("DATABASE HEALTH & FACILITY AUDIT")
    print("=" * 75)
    print(f"  Database Status:       {health.get('status')}")
    print(f"  PostGIS Connected:     {health.get('database_connected')}")
    print(f"  Industrial Facilities: {health.get('record_counts', {}).get('industrial_facilities', 0)} / {len(facilities)}")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(seed_facilities())
