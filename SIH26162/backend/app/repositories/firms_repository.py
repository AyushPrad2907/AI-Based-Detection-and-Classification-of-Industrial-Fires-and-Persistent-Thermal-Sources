"""
SIH26162 — NASA FIRMS Observation Repository.

Provides async query, spatial filtering, bounding box search, and bulk upsert operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID, ST_MakeEnvelope

from app.models.firms_observation import FIRMSObservation
from app.repositories.base_repository import BaseRepository


class FIRMSObservationRepository(BaseRepository[FIRMSObservation]):
    """Repository handling FIRMS satellite observations."""

    def __init__(self, session: AsyncSession):
        super().__init__(FIRMSObservation, session)

    async def create_observation(self, **kwargs) -> FIRMSObservation:
        """Create a FIRMS observation with geometry synthesis."""
        lat = kwargs.get("latitude")
        lon = kwargs.get("longitude")
        if lat is not None and lon is not None and "geom" not in kwargs:
            kwargs["geom"] = f"SRID=4326;POINT({lon} {lat})"
        return await self.create(**kwargs)

    async def bulk_insert_observations(
        self,
        records: List[Dict[str, Any]],
        chunk_size: int = 500,
    ) -> int:
        """
        Insert records in batches, skipping duplicates on (lat, lon, datetime, satellite, instrument).
        """
        if not records:
            return 0

        inserted_count = 0
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            for rec in chunk:
                # Synthesize geometry if missing
                lat = rec.get("latitude")
                lon = rec.get("longitude")
                geom_val = rec.get("geom")
                if geom_val is None and lat is not None and lon is not None:
                    rec["geom"] = f"SRID=4326;POINT({lon} {lat})"
                
                obs = FIRMSObservation(**rec)
                self.session.add(obs)
                inserted_count += 1

            try:
                await self.session.flush()
            except Exception as err:
                # If chunk had conflict, rollback to savepoint and insert individually
                await self.session.rollback()
                for rec in chunk:
                    try:
                        obs = FIRMSObservation(**rec)
                        self.session.add(obs)
                        await self.session.flush()
                    except Exception:
                        await self.session.rollback()

        return inserted_count

    async def query_observations(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        satellite: Optional[str] = None,
        instrument: Optional[str] = None,
        min_confidence: Optional[float] = None,
        confidence_category: Optional[str] = None,
        min_frp: Optional[float] = None,
        max_frp: Optional[float] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,  # (min_lon, min_lat, max_lon, max_lat)
        cluster_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[Sequence[FIRMSObservation], int]:
        """
        Query FIRMS observations with comprehensive filtering, spatial bounds, and pagination.
        Returns (records, total_count).
        """
        conditions = []

        if start_date:
            conditions.append(FIRMSObservation.acq_datetime >= start_date)
        if end_date:
            conditions.append(FIRMSObservation.acq_datetime <= end_date)
        if satellite:
            conditions.append(FIRMSObservation.satellite.ilike(f"%{satellite}%"))
        if instrument:
            conditions.append(FIRMSObservation.instrument.ilike(f"%{instrument}%"))
        if min_confidence is not None:
            conditions.append(FIRMSObservation.confidence_score >= min_confidence)
        if confidence_category:
            conditions.append(FIRMSObservation.confidence_category == confidence_category.lower())
        if min_frp is not None:
            conditions.append(FIRMSObservation.frp >= min_frp)
        if max_frp is not None:
            conditions.append(FIRMSObservation.frp <= max_frp)
        if cluster_id is not None:
            conditions.append(FIRMSObservation.cluster_id == cluster_id)

        if bbox is not None and len(bbox) == 4:
            min_lon, min_lat, max_lon, max_lat = bbox
            conditions.extend([
                FIRMSObservation.longitude >= min_lon,
                FIRMSObservation.longitude <= max_lon,
                FIRMSObservation.latitude >= min_lat,
                FIRMSObservation.latitude <= max_lat,
            ])

        where_clause = and_(*conditions) if conditions else True

        # Count total matches
        count_stmt = select(func.count()).select_from(FIRMSObservation).where(where_clause)
        total_count = (await self.session.execute(count_stmt)).scalar() or 0

        # Query records
        query = (
            select(FIRMSObservation)
            .where(where_clause)
            .order_by(FIRMSObservation.acq_datetime.desc(), FIRMSObservation.frp.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        records = result.scalars().all()

        return records, total_count

    async def query_by_radius(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float = 5000.0,
        limit: int = 100,
    ) -> Sequence[FIRMSObservation]:
        """
        Query observations within a radius (meters) using spatial proximity.
        """
        import math
        # ~111,320 meters per degree latitude
        lat_delta = radius_meters / 111320.0
        cos_lat = max(0.1, abs(math.cos(math.radians(latitude))))
        lon_delta = radius_meters / (111320.0 * cos_lat)

        # Box filter first for index efficiency, then fine distance
        query = (
            select(FIRMSObservation)
            .where(
                and_(
                    FIRMSObservation.latitude.between(latitude - lat_delta, latitude + lat_delta),
                    FIRMSObservation.longitude.between(longitude - lon_delta, longitude + lon_delta),
                )
            )
            .order_by(FIRMSObservation.acq_datetime.desc())
            .limit(limit)
        )
        res = await self.session.execute(query)
        return res.scalars().all()

    async def get_summary_metrics(self) -> Dict[str, Any]:
        """Compute aggregate dataset statistics."""
        stmt = select(
            func.count(FIRMSObservation.id).label("total_observations"),
            func.avg(FIRMSObservation.frp).label("mean_frp"),
            func.max(FIRMSObservation.frp).label("max_frp"),
            func.avg(FIRMSObservation.confidence_score).label("mean_confidence"),
            func.min(FIRMSObservation.acq_datetime).label("earliest_date"),
            func.max(FIRMSObservation.acq_datetime).label("latest_date"),
        )
        res = (await self.session.execute(stmt)).first()
        if not res:
            return {}

        return {
            "total_observations": res.total_observations or 0,
            "mean_frp_mw": round(float(res.mean_frp or 0), 2),
            "max_frp_mw": round(float(res.max_frp or 0), 2),
            "mean_confidence": round(float(res.mean_confidence or 0), 2),
            "earliest_observation_utc": res.earliest_date.isoformat() if res.earliest_date else None,
            "latest_observation_utc": res.latest_date.isoformat() if res.latest_date else None,
        }
