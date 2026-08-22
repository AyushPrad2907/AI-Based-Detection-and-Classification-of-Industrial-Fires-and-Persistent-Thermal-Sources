"""
SIH26162 — Health Check Response Schema.
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response model for the health check endpoint."""

    status: str
    service: str
    version: str
