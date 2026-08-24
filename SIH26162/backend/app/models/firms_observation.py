"""
SIH26162 — NASA FIRMS Observation ORM Model.

Stores raw and calibrated satellite active fire detections (VIIRS SNPP/NOAA-20, MODIS)
with PostGIS spatial Point geometries, spectral metrics, and cluster relationships.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.models.base import Base, TimestampMixin


class FIRMSObservation(Base, TimestampMixin):
    """
    NASA FIRMS Observation model.
    Represents an individual satellite active fire/thermal detection pixel.
    """
    __tablename__ = "firms_observations"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    
    # PostGIS Point geometry (WGS84 EPSG:4326)
    geom = mapped_column(Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=True)
    
    brightness_primary: Mapped[float] = mapped_column(Float, nullable=False)
    brightness_secondary: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    frp: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    confidence_category: Mapped[str] = mapped_column(String(20), nullable=False, default="nominal")
    
    acq_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    satellite: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    instrument: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    daynight: Mapped[str] = mapped_column(String(10), nullable=False, default="D")
    
    scan: Mapped[float] = mapped_column(Float, nullable=False, default=0.375)
    track: Mapped[float] = mapped_column(Float, nullable=False, default=0.375)
    
    source_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    cluster_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    
    # Relationships
    classifications = relationship("ThermalClassification", back_populates="observation", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="observation", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint(
            "latitude", "longitude", "acq_datetime", "satellite", "instrument",
            name="uq_firms_observation_pass"
        ),
        Index("idx_firms_coords_datetime", "latitude", "longitude", "acq_datetime"),
        Index("idx_firms_frp_conf", "frp", "confidence_score"),
    )

    def __repr__(self) -> str:
        return (
            f"<FIRMSObservation(id={self.id}, lat={self.latitude:.4f}, lon={self.longitude:.4f}, "
            f"frp={self.frp:.1f}MW, satellite='{self.satellite}')>"
        )
