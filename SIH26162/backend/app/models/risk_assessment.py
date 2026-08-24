"""
SIH26162 — Risk Assessment ORM Model.

Stores multi-criteria situational risk scores (0-100), hazard level categories,
subscore breakdowns (FRP, proximity, persistence, confidence, nocturnal), and explainable text reasons.
"""

from typing import List, Optional
from sqlalchemy import BigInteger, Float, ForeignKey, Integer, String, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class RiskAssessment(Base, TimestampMixin):
    """
    Risk Assessment model.
    Represents an explainable multi-factor hazard assessment for a classified fire/thermal event.
    """
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    
    classification_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("thermal_classifications.id", ondelete="CASCADE"), nullable=True, index=True
    )
    observation_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("firms_observations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # LOW, MODERATE, HIGH, CRITICAL
    
    frp_subscore: Mapped[float] = mapped_column(Float, nullable=False)
    industrial_proximity_subscore: Mapped[float] = mapped_column(Float, nullable=False)
    persistence_subscore: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_subscore: Mapped[float] = mapped_column(Float, nullable=False)
    nocturnal_subscore: Mapped[float] = mapped_column(Float, nullable=False)
    
    reasons: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    
    # Relationships
    classification = relationship("ThermalClassification", back_populates="risk_assessment")
    observation = relationship("FIRMSObservation", back_populates="risk_assessments")

    __table_args__ = (
        Index("idx_risk_level_score", "risk_level", "risk_score"),
    )

    def __repr__(self) -> str:
        return f"<RiskAssessment(id={self.id}, score={self.risk_score:.1f}, level='{self.risk_level}')>"
