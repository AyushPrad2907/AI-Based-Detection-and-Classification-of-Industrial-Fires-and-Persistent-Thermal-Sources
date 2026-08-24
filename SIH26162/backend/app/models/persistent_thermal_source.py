"""
SIH26162 — Persistent Thermal Source ORM Model.

Stores spatio-temporal DBSCAN clusters identified as recurring industrial thermal sources.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.models.base import Base, TimestampMixin


class PersistentThermalSource(Base, TimestampMixin):
    """
    Persistent Thermal Source model.
    Represents a spatial cluster that exhibits recurring high-temperature satellite passes.
    """
    __tablename__ = "persistent_thermal_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cluster_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    
    centroid_lat: Mapped[float] = mapped_column(Float, nullable=False)
    centroid_lon: Mapped[float] = mapped_column(Float, nullable=False)
    
    # PostGIS Point geometry (WGS84 EPSG:4326)
    centroid_geom = mapped_column(Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=True)
    
    observation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    first_seen_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_seen_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    persistence_duration_days: Mapped[float] = mapped_column(Float, nullable=False)
    
    mean_frp_mw: Mapped[float] = mapped_column(Float, nullable=False)
    max_frp_mw: Mapped[float] = mapped_column(Float, nullable=False)
    mean_brightness_kelvin: Mapped[float] = mapped_column(Float, nullable=False)
    mean_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    night_observation_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    spatial_radius_meters: Mapped[float] = mapped_column(Float, nullable=False)
    is_persistent: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    nearest_industrial_facility_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("industrial_facilities.id", ondelete="SET NULL"), nullable=True
    )
    
    nearest_facility = relationship("IndustrialFacility", foreign_keys=[nearest_industrial_facility_id])

    __table_args__ = (
        Index("idx_thermal_source_centroid", "centroid_lat", "centroid_lon"),
        Index("idx_thermal_source_obs_count", "observation_count"),
        Index("idx_thermal_source_persistence", "is_persistent"),
    )

    def __repr__(self) -> str:
        return f"<PersistentThermalSource(cluster_id={self.cluster_id}, passes={self.observation_count}, persistent={self.is_persistent})>"
