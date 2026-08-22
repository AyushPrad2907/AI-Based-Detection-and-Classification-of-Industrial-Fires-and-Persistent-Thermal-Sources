"""
SIH26162 — API Endpoint Tests (Placeholder).

Placeholder tests for fire detection, thermal source,
and geospatial endpoints. Will be expanded in Phase 3.
"""


def test_fires_placeholder(client):
    """Test that fire endpoint returns placeholder response."""
    response = client.get("/api/v1/fires/")
    assert response.status_code == 200
    assert response.json()["status"] == "placeholder"


def test_thermal_placeholder(client):
    """Test that thermal endpoint returns placeholder response."""
    response = client.get("/api/v1/thermal/")
    assert response.status_code == 200
    assert response.json()["status"] == "placeholder"


def test_geospatial_placeholder(client):
    """Test that geospatial endpoint returns placeholder response."""
    response = client.get("/api/v1/geospatial/")
    assert response.status_code == 200
    assert response.json()["status"] == "placeholder"
