"""
SIH26162 — Integration Tests for Phase 2 API Endpoints.
"""

from unittest.mock import patch
import pytest


def test_fires_status_endpoint(client):
    response = client.get("/api/v1/fires/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True
    assert "classes" in data
    assert data["features_count"] > 0


def test_fires_classify_endpoint(client):
    mock_osm = {
        "is_industrial_nearby": True,
        "min_distance_m": 350.0,
        "min_distance_km": 0.35,
        "nearest_facility_name": "Petroleum Refinery",
        "nearest_facility_type": "petroleum_refinery",
        "total_facilities_in_radius": 1,
        "facilities": [],
        "query_latitude": 22.5,
        "query_longitude": 88.3,
        "search_radius_m": 5000,
        "status": "success",
    }

    with patch("app.services.osm_service.OSMService.get_industrial_context", return_value=mock_osm):
        payload = {
            "latitude": 22.5,
            "longitude": 88.3,
            "brightness_primary": 340.0,
            "brightness_secondary": 290.0,
            "frp": 35.0,
            "confidence": 90.0,
            "daynight": "N",
            "query_osm": True,
        }
        response = client.post("/api/v1/fires/classify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "predicted_class" in data
        assert "classification_confidence" in data
        assert "risk_score" in data
        assert "risk_level" in data
        assert isinstance(data["reasons"], list)
        assert len(data["reasons"]) > 0


def test_fires_batch_classify_endpoint(client):
    payload = {
        "observations": [
            {
                "latitude": 20.0,
                "longitude": 78.0,
                "brightness_primary": 330.0,
                "frp": 10.0,
                "confidence": 70.0,
            },
            {
                "latitude": 21.0,
                "longitude": 79.0,
                "brightness_primary": 350.0,
                "frp": 40.0,
                "confidence": 95.0,
            },
        ],
        "query_osm": False,
    }
    response = client.post("/api/v1/fires/classify/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_processed"] == 2
    assert len(data["results"]) == 2


def test_thermal_sources_endpoint(client):
    response = client.get("/api/v1/thermal/sources?min_observations=2&persistent_only=true")
    assert response.status_code == 200
    data = response.json()
    assert "total_clusters" in data
    assert "persistent_sources_count" in data
    assert isinstance(data["clusters"], list)


def test_thermal_clusters_endpoint(client):
    response = client.get("/api/v1/thermal/clusters")
    assert response.status_code == 200
    data = response.json()
    assert "clusters" in data


def test_geospatial_industrial_context_endpoint(client):
    mock_osm = {
        "is_industrial_nearby": False,
        "min_distance_m": 5000.0,
        "min_distance_km": 5.0,
        "nearest_facility_name": None,
        "nearest_facility_type": None,
        "total_facilities_in_radius": 0,
        "facilities": [],
        "query_latitude": 28.0,
        "query_longitude": 77.0,
        "search_radius_m": 5000,
        "status": "no_facilities_found",
    }

    with patch("app.services.osm_service.OSMService.get_industrial_context", return_value=mock_osm):
        payload = {
            "latitude": 28.0,
            "longitude": 77.0,
            "radius_m": 5000,
        }
        response = client.post("/api/v1/geospatial/industrial-context", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["is_industrial_nearby"] is False
        assert data["min_distance_m"] == 5000.0
