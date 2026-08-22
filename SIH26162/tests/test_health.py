"""
SIH26162 — Health Endpoint Tests.

Tests for the /api/v1/health endpoint.
"""


def test_health_check(client):
    """Test that the health endpoint returns a healthy status."""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SIH26162 API"
    assert data["version"] == "0.1.0"


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
