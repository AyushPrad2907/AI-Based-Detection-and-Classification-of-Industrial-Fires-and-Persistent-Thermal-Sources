import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.main import app
from app.core.database import get_db

@pytest.fixture
def mock_db_session():
    mock_session = MagicMock()
    # Provide a simple mock behavior if needed
    yield mock_session

@pytest.fixture
def override_db(mock_db_session):
    async def _get_db_override():
        yield mock_db_session

    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
async def async_client(override_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

@pytest.mark.anyio
async def test_health_endpoint(async_client):
    response = await async_client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "service" in data

@pytest.mark.anyio
@patch("app.api.v1.endpoints.fires.classification_service.classify_thermal_source")
async def test_classify_endpoint_success(mock_classify, async_client):
    mock_classify.return_value = {
        "latitude": 34.0522,
        "longitude": -118.2437,
        "predicted_class": "industrial_fire",
        "classification_confidence": 0.95,
        "class_probabilities": {"industrial_fire": 0.95, "wildfire": 0.05},
        "risk_score": 85.0,
        "risk_level": "HIGH",
        "risk_breakdown": {
            "frp_subscore": 10.0,
            "industrial_proximity_subscore": 5.0,
            "persistence_subscore": 0.0,
            "confidence_subscore": 2.0,
            "nocturnal_subscore": 0.0
        },
        "is_persistent_source": False,
        "thermal_parameters": {},
        "reasons": ["High FRP"]
    }

    payload = {
        "latitude": 34.0522,
        "longitude": -118.2437,
        "brightness_primary": 350.5,
        "brightness_secondary": 290.0,
        "frp": 150.0,
        "confidence": 99.0,
        "daynight": "D",
        "persist": False
    }

    response = await async_client.post("/api/v1/fires/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_class"] == "industrial_fire"
    assert data["risk_score"] == 85.0
    assert data["risk_level"] == "HIGH"
    assert "reasons" in data

@pytest.mark.anyio
async def test_classify_endpoint_validation_error(async_client):
    payload = {
        "latitude": 900.0, # Invalid lat
        "longitude": -118.2437,
        "brightness_primary": 350.5
    }
    response = await async_client.post("/api/v1/fires/classify", json=payload)
    assert response.status_code == 422 # Unprocessable Entity

@pytest.mark.anyio
@patch("app.api.v1.endpoints.fires.FIRMSObservationRepository.get_by_id")
async def test_get_fire_by_id_success(mock_get_by_id, async_client):
    mock_record = MagicMock()
    mock_record.id = 1
    mock_record.latitude = 34.0522
    mock_record.longitude = -118.2437
    mock_record.brightness_primary = 350.5
    mock_record.brightness_secondary = 290.0
    mock_record.frp = 150.0
    mock_record.confidence_score = 99.0
    mock_record.acq_datetime = datetime(2026, 8, 29, 12, 0, 0)
    mock_record.satellite = "MODIS"
    mock_record.instrument = "Aqua"
    mock_record.cluster_id = 1
    mock_get_by_id.return_value = mock_record

    response = await async_client.get("/api/v1/fires/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["latitude"] == 34.0522
    assert data["satellite"] == "MODIS"

@pytest.mark.anyio
@patch("app.api.v1.endpoints.fires.FIRMSObservationRepository.get_by_id")
async def test_get_fire_by_id_not_found(mock_get_by_id, async_client):
    mock_get_by_id.return_value = None
    response = await async_client.get("/api/v1/fires/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Observation #999 not found in database."

@pytest.mark.anyio
@patch("app.api.v1.endpoints.fires.classification_service.batch_classify")
async def test_batch_classify_endpoint_success(mock_batch_classify, async_client):
    mock_batch_classify.return_value = [
        {
            "latitude": 34.0522,
            "longitude": -118.2437,
            "predicted_class": "industrial_fire",
            "classification_confidence": 0.95,
            "class_probabilities": {},
            "risk_score": 85.0,
            "risk_level": "HIGH",
            "risk_breakdown": {
                "frp_subscore": 10.0,
                "industrial_proximity_subscore": 5.0,
                "persistence_subscore": 0.0,
                "confidence_subscore": 2.0,
                "nocturnal_subscore": 0.0
            },
            "is_persistent_source": False,
            "thermal_parameters": {},
            "reasons": []
        }
    ]

    payload = {
        "observations": [
            {
                "latitude": 34.0522,
                "longitude": -118.2437,
                "brightness_primary": 350.5,
                "brightness_secondary": 290.0,
                "frp": 150.0,
                "confidence": 99.0,
                "daynight": "D"
            }
        ]
    }
    response = await async_client.post("/api/v1/fires/classify/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_processed"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["predicted_class"] == "industrial_fire"

@pytest.mark.anyio
async def test_batch_classify_validation_error(async_client):
    payload = {
        "observations": [
            {
                "latitude": "invalid_lat",
                "longitude": -118.2437
            }
        ]
    }
    response = await async_client.post("/api/v1/fires/classify/batch", json=payload)
    assert response.status_code == 422

@pytest.mark.anyio
@patch("app.api.v1.endpoints.thermal.ThermalSourceRepository.query_sources")
async def test_thermal_persistent_sources_success(mock_query_sources, async_client):
    mock_source = MagicMock()
    mock_source.cluster_id = 100
    mock_source.centroid_lat = 40.7128
    mock_source.centroid_lon = -74.0060
    mock_source.observation_count = 10
    mock_source.first_seen_utc = datetime(2026, 8, 20)
    mock_source.last_seen_utc = datetime(2026, 8, 29)
    mock_source.persistence_duration_days = 9.0
    mock_source.mean_frp_mw = 50.0
    mock_source.max_frp_mw = 100.0
    mock_source.mean_brightness_kelvin = 320.0
    mock_source.mean_confidence = 85.0
    mock_source.night_observation_ratio = 0.5
    mock_source.spatial_radius_meters = 200.0
    mock_source.is_persistent = True

    mock_query_sources.return_value = ([mock_source], 1)

    response = await async_client.get("/api/v1/thermal/sources?min_observations=5")
    assert response.status_code == 200
    data = response.json()
    assert data["total_clusters"] == 1
    assert data["persistent_sources_count"] == 1
    assert len(data["clusters"]) == 1
    assert data["clusters"][0]["cluster_id"] == 100
    assert data["clusters"][0]["centroid_latitude"] == 40.7128

@pytest.mark.anyio
@patch("app.api.v1.endpoints.geospatial.osm_service.get_industrial_context")
async def test_geospatial_industrial_context_success(mock_osm, async_client):
    mock_osm.return_value = {
        "is_industrial_nearby": True,
        "min_distance_m": 500.0,
        "min_distance_km": 0.5,
        "nearest_facility_name": "Test Factory",
        "nearest_facility_type": "industrial",
        "total_facilities_in_radius": 1,
        "facilities": [
            {
                "osm_id": 12345,
                "osm_type": "node",
                "name": "Test Factory",
                "facility_type": "industrial",
                "latitude": 40.7150,
                "longitude": -74.0050,
                "distance_meters": 500.0,
                "tags": {}
            }
        ],
        "query_latitude": 40.7128,
        "query_longitude": -74.0060,
        "search_radius_m": 1000,
        "status": "success"
    }

    payload = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "radius_m": 1000
    }
    response = await async_client.post("/api/v1/geospatial/industrial-context", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_industrial_nearby"] is True
    assert data["nearest_facility_name"] == "Test Factory"
    assert data["total_facilities_in_radius"] == 1
    assert len(data["facilities"]) == 1
    assert data["facilities"][0]["name"] == "Test Factory"

@pytest.mark.anyio
async def test_geospatial_industrial_context_validation_error(async_client):
    payload = {
        "latitude": 40.7128,
        # missing longitude
        "radius_m": 1000
    }
    response = await async_client.post("/api/v1/geospatial/industrial-context", json=payload)
    assert response.status_code == 422
