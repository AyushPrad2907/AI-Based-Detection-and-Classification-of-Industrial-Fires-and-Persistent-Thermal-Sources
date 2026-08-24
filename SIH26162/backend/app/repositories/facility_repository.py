"""
SIH26162 — Industrial Facility Repository.

Provides async query and spatial proximity lookups for OpenStreetMap industrial assets.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.industrial_facility import IndustrialFacility
from app.repositories.base_repository import BaseRepository


class IndustrialFacilityRepository(BaseRepository[IndustrialFacility]):
    """Repository handling OpenStreetMap industrial facilities."""

    def __init__(self, session: AsyncSession):
        super().__init__(IndustrialFacility, session)

    async def get_by_osm_id(self, osm_id: int) -> Optional[IndustrialFacility]:
        """Fetch facility by OpenStreetMap ID."""
        stmt = select(IndustrialFacility).where(IndustrialFacility.osm_id == osm_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def bulk_upsert_facilities(
        self,
        facilities: List[Dict[str, Any]],
    ) -> int:
        """Upsert industrial facilities from OSM Overpass results."""
        count = 0
        for f in facilities:
            osm_id = f.get("osm_id")
            existing = None
            if osm_id:
                existing = await self.get_by_osm_id(osm_id)

            lat = f.get("latitude")
            lon = f.get("longitude")
            geom_val = f"SRID=4326;POINT({lon} {lat})" if lat is not None and lon is not None else None

            data = {
                "osm_id": osm_id,
                "osm_type": f.get("osm_type", "node"),
                "name": f.get("name", "Industrial Facility"),
                "facility_type": f.get("facility_type", "industrial"),
                "latitude": lat,
                "longitude": lon,
                "geom": geom_val,
                "tags": f.get("tags"),
            }

            if existing:
                for k, v in data.items():
                    setattr(existing, k, v)
            else:
                new_fac = IndustrialFacility(**data)
                self.session.add(new_fac)
            count += 1

        await self.session.flush()
        return count
