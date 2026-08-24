"""
SIH26162 — Industrial Facility ORM Model.

Stores OpenStreetMap-derived industrial facilities, factories, power stations,
flare units, and industrial land-use zones with PostGIS Point geometries.
"""

from typing import Optional, Dict, Any
from sqlalchemy import BigInteger, Float, Integer, String, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.models.base import Base, TimestampMixin


class IndustrialFacility(Base, TimestampMixin):
    """
    Industrial Facility model.
    Represents an infrastructure asset queried from OpenStreetMap / Overpass.
    """
    __tablename__ = "industrial_facilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    osm_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, nullable=True, index=True)
    osm_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="Unnamed Industrial Facility")
    facility_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    
    # PostGIS Point geometry (WGS84 EPSG:4326)
    geom = mapped_column(Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=True)
    
    tags: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("idx_facility_lat_lon", "latitude", "longitude"),
        Index("idx_facility_type", "facility_type"),
    )

    def __repr__(self) -> str:
        return f"<IndustrialFacility(id={self.id}, name='{self.name}', type='{self.facility_type}')>"
