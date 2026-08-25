"""
SIH26162 — Unit Tests for OpenStreetMap / Overpass Service.
Phase 6: Extended timeout, HTTP error, empty/malformed response, and bounded timing tests.
"""

import time
from unittest.mock import MagicMock, patch
import pytest
import httpx

from app.services.osm_service import OSMService, OSM_READ_TIMEOUT, OSM_CONNECT_TIMEOUT


MOCK_OVERPASS_SUCCESS_RESPONSE = {
    "version": 0.6,
    "elements": [
        {
            "type": "way",
            "id": 1234567,
            "center": {"lat": 28.6150, "lon": 77.2100},
            "tags": {
                "name": "Central Thermal Power Station",
                "power": "plant",
                "landuse": "industrial",
            },
        },
        {
            "type": "node",
            "id": 7654321,
            "lat": 28.6200,
            "lon": 77.2200,
            "tags": {
                "name": "Chemical Manufacturing Plant",
                "man_made": "works",
            },
        },
    ],
}


@pytest.mark.anyio
async def test_osm_service_async_success():
    service = OSMService()
    service.clear_cache()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_OVERPASS_SUCCESS_RESPONSE

    with patch.object(httpx.AsyncClient, "post", return_value=mock_resp):
        res = await service.get_industrial_context(latitude=28.6139, longitude=77.2090, radius_m=5000)

        assert res["status"] == "success"
        assert res["is_industrial_nearby"] is True
        assert res["total_facilities_in_radius"] == 2
        assert "Central Thermal Power Station" in res["nearest_facility_name"]
        assert res["min_distance_m"] < 1000.0


@pytest.mark.anyio
async def test_osm_service_async_cache():
    service = OSMService()
    service.clear_cache()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_OVERPASS_SUCCESS_RESPONSE

    with patch.object(httpx.AsyncClient, "post", return_value=mock_resp) as mock_post:
        # First call
        res1 = await service.get_industrial_context(latitude=28.6139, longitude=77.2090, radius_m=5000)
        assert mock_post.call_count == 1

        # Second identical call should hit in-memory spatial cache
        res2 = await service.get_industrial_context(latitude=28.6139, longitude=77.2090, radius_m=5000)
        assert mock_post.call_count == 1
        assert res1 == res2


@pytest.mark.anyio
async def test_osm_service_fallback_on_network_error():
    service = OSMService()
    service.clear_cache()

    with patch.object(httpx.AsyncClient, "post", side_effect=httpx.ConnectError("Connection refused")):
        res = await service.get_industrial_context(latitude=28.6139, longitude=77.2090, radius_m=5000)

        assert res["status"] == "offline_fallback"
        assert res["is_industrial_nearby"] is False
        assert res["total_facilities_in_radius"] == 0


# ============================================================================
# Phase 6 Additional Tests — Timeout & Error Resilience
# ============================================================================

@pytest.mark.anyio
async def test_osm_service_fallback_on_connect_timeout():
    """ConnectTimeout must return offline_fallback, not raise."""
    service = OSMService()
    service.clear_cache()

    with patch.object(httpx.AsyncClient, "post", side_effect=httpx.ConnectTimeout("connect timed out")):
        res = await service.get_industrial_context(latitude=20.0, longitude=78.5, radius_m=5000)

    assert res["status"] == "offline_fallback"
    assert res["is_industrial_nearby"] is False


@pytest.mark.anyio
async def test_osm_service_fallback_on_read_timeout():
    """ReadTimeout must return offline_fallback, not raise."""
    service = OSMService()
    service.clear_cache()

    with patch.object(httpx.AsyncClient, "post", side_effect=httpx.ReadTimeout("read timed out")):
        res = await service.get_industrial_context(latitude=20.0, longitude=78.5, radius_m=5000)

    assert res["status"] == "offline_fallback"
    assert res["is_industrial_nearby"] is False


@pytest.mark.anyio
async def test_osm_service_fallback_on_http_503():
    """HTTP 5xx must return service_unavailable fallback, not raise."""
    service = OSMService()
    service.clear_cache()

    mock_resp = MagicMock()
    mock_resp.status_code = 503

    with patch.object(httpx.AsyncClient, "post", return_value=mock_resp):
        res = await service.get_industrial_context(latitude=20.0, longitude=78.5, radius_m=5000)

    assert "service_unavailable" in res["status"]
    assert res["is_industrial_nearby"] is False


@pytest.mark.anyio
async def test_osm_service_empty_elements_returns_no_facilities_found():
    """Empty elements list returns no_facilities_found, not an error."""
    service = OSMService()
    service.clear_cache()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"version": 0.6, "elements": []}

    with patch.object(httpx.AsyncClient, "post", return_value=mock_resp):
        res = await service.get_industrial_context(latitude=20.0, longitude=78.5, radius_m=5000)

    assert res["status"] == "no_facilities_found"
    assert res["total_facilities_in_radius"] == 0
    assert res["is_industrial_nearby"] is False


@pytest.mark.anyio
async def test_osm_service_malformed_json_returns_fallback():
    """Malformed JSON from Overpass must return a safe fallback, never raise."""
    service = OSMService()
    service.clear_cache()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.side_effect = ValueError("No JSON object could be decoded")

    with patch.object(httpx.AsyncClient, "post", return_value=mock_resp):
        res = await service.get_industrial_context(latitude=20.0, longitude=78.5, radius_m=5000)

    assert res["status"] == "offline_fallback"
    assert res["is_industrial_nearby"] is False


def test_osm_timeout_is_bounded():
    """Verify configured OSM timeouts are ≤ 3s each to prevent dashboard blocking."""
    assert OSM_CONNECT_TIMEOUT <= 3.0, f"OSM connect timeout {OSM_CONNECT_TIMEOUT}s exceeds 3s limit"
    assert OSM_READ_TIMEOUT <= 3.0, f"OSM read timeout {OSM_READ_TIMEOUT}s exceeds 3s limit"
