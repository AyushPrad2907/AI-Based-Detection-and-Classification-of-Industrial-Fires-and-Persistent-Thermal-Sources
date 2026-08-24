"""
SIH26162 — ML Model Metadata ORM Model.

Tracks trained machine learning model runs, versions, evaluation benchmarks,
feature sets, and artifact locations in the database.
"""

from typing import List, Optional
from sqlalchemy import Boolean, Float, Integer, String, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class MLModelMetadata(Base, TimestampMixin):
    """
    ML Model Metadata model.
    Maintains provenance and metrics for trained fire classification models.
    """
    __tablename__ = "ml_model_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)  # random_forest, gradient_boosting
    version: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    dataset_size: Mapped[int] = mapped_column(Integer, nullable=False)
    train_accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    test_accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    test_f1_macro: Mapped[float] = mapped_column(Float, nullable=False)
    test_roc_auc: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    features_used: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    artifact_path: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("idx_model_type_version", "model_type", "version"),
    )

    def __repr__(self) -> str:
        return f"<MLModelMetadata(version='{self.version}', test_acc={self.test_accuracy:.4f}, active={self.is_active})>"
