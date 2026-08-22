"""
SIH26162 — Thermal Source Schemas (Placeholder).

These schemas will define the request/response models for
thermal source monitoring endpoints.

NOT YET IMPLEMENTED — will be defined in Phase 3.
"""

from pydantic import BaseModel


class ThermalSourceBase(BaseModel):
    """Base schema for thermal source data. To be expanded."""

    # Placeholder fields — will be defined when classification model is ready
    # source_type: str  (industrial, wildfire, agricultural, power_plant, etc.)
    # latitude: float
    # longitude: float
    # temperature_kelvin: float
    # persistence_days: int
    pass
