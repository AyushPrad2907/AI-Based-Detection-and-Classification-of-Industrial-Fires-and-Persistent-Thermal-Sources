import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.alert_stream import alert_stream_service
from app.services.poller_service import poller_service


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.mark.anyio
async def test_alerts_recent_endpoint(async_client):
    response = await async_client.get("/api/v1/alerts/recent")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_alerts_simulate_endpoint(async_client):
    response = await async_client.post(
        "/api/v1/alerts/simulate",
        json={"zone_name": "Jamnagar", "acute_fire": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "alert" in data
    alert = data["alert"]
    assert alert["predicted_class"] == "industrial_fire"
    assert alert["risk_level"] in ("HIGH", "CRITICAL")
    assert alert["frp_mw"] > 0
    assert "Jamnagar" in alert["nearest_facility"] or "Jamnagar" in alert["location_name"]


@pytest.mark.anyio
async def test_poller_lifecycle_endpoints(async_client):
    # Check status
    status_resp = await async_client.get("/api/v1/alerts/poller/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert "running" in status_data
    assert "interval_seconds" in status_data

    # Start poller
    start_resp = await async_client.post("/api/v1/alerts/poller/start?interval_seconds=15")
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "started"

    # Stop poller
    stop_resp = await async_client.post("/api/v1/alerts/poller/stop")
    assert stop_resp.status_code == 200
    assert stop_resp.json()["status"] == "stopped"


@pytest.mark.anyio
async def test_custom_broadcast_endpoint(async_client):
    payload = {
        "predicted_class": "industrial_fire",
        "latitude": 22.4707,
        "longitude": 70.0577,
        "frp_mw": 150.0,
        "risk_score": 95.0,
        "risk_level": "CRITICAL",
        "nearest_facility": "Test Refinery",
        "facility_distance_km": 0.4,
        "summary": "Custom test acute fire",
    }
    response = await async_client.post("/api/v1/alerts/broadcast", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "broadcasted"
    assert data["alert"]["predicted_class"] == "industrial_fire"

    # Check that it appears in recent
    recent_resp = await async_client.get("/api/v1/alerts/recent")
    recent = recent_resp.json()
    assert len(recent) > 0
    assert recent[0]["nearest_facility"] == "Test Refinery"
