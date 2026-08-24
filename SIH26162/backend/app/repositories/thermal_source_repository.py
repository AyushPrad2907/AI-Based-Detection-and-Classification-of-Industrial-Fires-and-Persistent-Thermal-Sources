"""
SIH26162 — Persistent Thermal Source Repository.

Provides async query and spatial lookups for clustered persistent thermal sources.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.persistent_thermal_source import PersistentThermalSource
from app.repositories.base_repository import BaseRepository


class ThermalSourceRepository(BaseRepository[PersistentThermalSource]):
    """Repository handling persistent thermal sources and clusters."""

    def __init__(self, session: AsyncSession):
        super().__init__(PersistentThermalSource, session)

    async def get_by_cluster_id(self, cluster_id: int) -> Optional[PersistentThermalSource]:
        """Fetch thermal source by cluster ID."""
        stmt = select(PersistentThermalSource).where(PersistentThermalSource.cluster_id == cluster_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def query_sources(
        self,
        persistent_only: bool = True,
        min_observations: int = 1,
        min_frp: Optional[float] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[Sequence[PersistentThermalSource], int]:
        """
        Query persistent sources with filtering and spatial bounds.
        """
        conditions = [PersistentThermalSource.observation_count >= min_observations]

        if persistent_only:
            conditions.append(PersistentThermalSource.is_persistent.is_(True))
        if min_frp is not None:
            conditions.append(PersistentThermalSource.mean_frp_mw >= min_frp)

        if bbox is not None and len(bbox) == 4:
            min_lon, min_lat, max_lon, max_lat = bbox
            conditions.extend([
                PersistentThermalSource.centroid_lon >= min_lon,
                PersistentThermalSource.centroid_lon <= max_lon,
                PersistentThermalSource.centroid_lat >= min_lat,
                PersistentThermalSource.centroid_lat <= max_lat,
            ])

        where_clause = and_(*conditions)

        count_stmt = select(func.count()).select_from(PersistentThermalSource).where(where_clause)
        total_count = (await self.session.execute(count_stmt)).scalar() or 0

        query = (
            select(PersistentThermalSource)
            .where(where_clause)
            .order_by(PersistentThermalSource.observation_count.desc(), PersistentThermalSource.mean_frp_mw.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return result.scalars().all(), total_count

    async def bulk_upsert_clusters(
        self,
        clusters: List[Dict[str, Any]],
    ) -> int:
        """
        Upsert persistent thermal clusters from ThermalDetector output.
        """
        from datetime import datetime

        def _to_dt(val):
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val)
                except Exception:
                    return datetime.utcnow()
            return val

        count = 0
        for c in clusters:
            cluster_id = c.get("cluster_id")
            existing = await self.get_by_cluster_id(cluster_id)
            lat = c.get("centroid_lat")
            lon = c.get("centroid_lon")
            geom_val = f"SRID=4326;POINT({lon} {lat})" if lat is not None and lon is not None else None

            data = {
                "cluster_id": cluster_id,
                "centroid_lat": lat,
                "centroid_lon": lon,
                "centroid_geom": geom_val,
                "observation_count": c.get("observation_count", 0),
                "first_seen_utc": _to_dt(c.get("first_seen_utc")),
                "last_seen_utc": _to_dt(c.get("last_seen_utc")),
                "persistence_duration_days": c.get("persistence_duration_days", 0.0),
                "mean_frp_mw": c.get("mean_frp_mw", 0.0),
                "max_frp_mw": c.get("max_frp_mw", 0.0),
                "mean_brightness_kelvin": c.get("mean_brightness_kelvin", 0.0),
                "mean_confidence": c.get("mean_confidence", 0.0),
                "night_observation_ratio": c.get("night_observation_ratio", 0.0),
                "spatial_radius_meters": c.get("spatial_radius_meters", 0.0),
                "is_persistent": c.get("is_persistent", True),
            }

            if existing:
                for k, v in data.items():
                    setattr(existing, k, v)
            else:
                new_source = PersistentThermalSource(**data)
                self.session.add(new_source)
            count += 1

        await self.session.flush()
        return count
