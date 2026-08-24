"""
SIH26162 — Thermal Classification ORM Model.

Stores ML model inference outputs (predicted class, class probability distribution,
confidence score, and model version) linked to FIRMS observations.
"""

from typing import Dict, Any, Optional
from sqlalchemy import BigInteger, Boolean, Float, ForeignKey, Integer, String, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ThermalClassification(Base, TimestampMixin):
    """
    Thermal Classification model.
    Stores ML classification predictions for thermal anomaly events.
    """
    __tablename__ = "thermal_classifications"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    
    observation_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("firms_observations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    
    predicted_class: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Probability distribution across all 5 classes
    class_probabilities: Mapped[Dict[str, float]] = mapped_column(JSON, nullable=False)
    
    model_version: Mapped[str] = mapped_column(String(50), nullable=False, default="random_forest_v1", index=True)
    is_weak_label: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    observation = relationship("FIRMSObservation", back_populates="classifications")
    risk_assessment = relationship("RiskAssessment", back_populates="classification", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_classification_class_conf", "predicted_class", "confidence"),
        Index("idx_classification_coords", "latitude", "longitude"),
    )

    def __repr__(self) -> str:
        return (
            f"<ThermalClassification(id={self.id}, class='{self.predicted_class}', "
            f"conf={self.confidence:.2f}, model='{self.model_version}')>"
        )
