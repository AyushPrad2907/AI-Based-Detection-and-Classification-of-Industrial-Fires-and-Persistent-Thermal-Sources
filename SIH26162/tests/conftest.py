"""
SIH26162 — Pytest Configuration and Fixtures.

Shared fixtures for backend and ML tests.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    return TestClient(app)
