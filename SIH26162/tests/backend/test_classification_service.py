"""
SIH26162 — Unit Tests for Classification Service.
"""

from unittest.mock import MagicMock, patch
import pytest

from app.services.classification_service import ClassificationService
from app.services.osm_service import OSMService


@pytest.mark.anyio
async def test_classification_service_inference():
    service = ClassificationService()
    assert service.is_model_ready() is True

    # Mock OSM to isolate tests
    mock_osm_result = {
        "is_industrial_nearby": True,
        "min_distance_m": 450.0,
        "min_distance_km": 0.45,
        "nearest_facility_name": "Steel Foundry Plant",
        "nearest_facility_type": "metal_works",
        "total_facilities_in_radius": 1,
        "facilities": [],
        "query_latitude": 22.5,
        "query_longitude": 88.3,
        "search_radius_m": 5000,
        "status": "success",
    }

    with patch.object(service.osm_service, "get_industrial_context", return_value=mock_osm_result):
        res = await service.classify_thermal_source(
            latitude=22.5,
            longitude=88.3,
            brightness_primary=345.0,
            brightness_secondary=295.0,
            frp=45.0,
            confidence=95.0,
            daynight="N",
            query_osm=True,
        )

        assert "predicted_class" in res
        assert "classification_confidence" in res
        assert "class_probabilities" in res
        assert "risk_score" in res
        assert "risk_level" in res
        assert "reasons" in res
        assert res["industrial_context"]["nearest_facility_name"] == "Steel Foundry Plant"


@pytest.mark.anyio
async def test_classification_service_batch():
    service = ClassificationService()
    observations = [
        {"latitude": 20.0, "longitude": 80.0, "frp": 30.0, "confidence": 90.0},
        {"latitude": 25.0, "longitude": 85.0, "frp": 5.0, "confidence": 50.0},
    ]

    results = await service.batch_classify(observations, query_osm=False)
    assert len(results) == 2
    assert all("predicted_class" in r for r in results)
