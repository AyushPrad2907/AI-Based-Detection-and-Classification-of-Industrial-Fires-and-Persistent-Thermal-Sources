"""
SIH26162 — Fire Detection Schemas (Placeholder).

These schemas will define the request/response models for
fire detection endpoints.

NOT YET IMPLEMENTED — will be defined in Phase 3.
"""

from pydantic import BaseModel


class FireDetectionBase(BaseModel):
    """Base schema for fire detection data. To be expanded."""

    # Placeholder fields — will be defined when FIRMS data model is finalized
    # latitude: float
    # longitude: float
    # brightness: float
    # confidence: str
    # fire_type: str
    pass
