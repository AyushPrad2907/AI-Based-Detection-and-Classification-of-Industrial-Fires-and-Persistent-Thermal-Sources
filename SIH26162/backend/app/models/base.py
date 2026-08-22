"""
SIH26162 — SQLAlchemy Base Model.

Provides the declarative base for all ORM models.
Database tables will be defined in Phase 3.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    All models should inherit from this class:

        class FireDetection(Base):
            __tablename__ = "fire_detections"
            ...
    """
    pass
