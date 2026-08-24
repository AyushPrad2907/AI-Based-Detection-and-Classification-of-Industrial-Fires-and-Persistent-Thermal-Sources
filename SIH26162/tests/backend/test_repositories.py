"""
Unit and integration tests for database repository CRUD operations.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.base import Base
from app.repositories.firms_repository import FIRMSObservationRepository
from app.repositories.thermal_source_repository import ThermalSourceRepository
from app.repositories.classification_repository import ClassificationRepository
from app.repositories.facility_repository import IndustrialFacilityRepository


@pytest.fixture
async def async_db_session():
    """Provides an isolated in-memory test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.anyio
async def test_firms_repository_crud_and_query(async_db_session: AsyncSession):
    repo = FIRMSObservationRepository(async_db_session)

    # 1. Bulk insert
    records = [
        {
            "latitude": 23.76 + i * 0.01,
            "longitude": 86.40 + i * 0.01,
            "brightness_primary": 330.0 + i * 2.0,
            "frp": 10.0 + i * 5.0,
            "confidence_score": 75.0 + i * 2.0,
            "confidence_category": "nominal" if i < 3 else "high",
            "acq_datetime": datetime(2026, 8, 24, 10, 0) + timedelta(hours=i),
            "satellite": "VIIRS_SNPP_NRT" if i % 2 == 0 else "VIIRS_NOAA20_NRT",
            "instrument": "VIIRS",
            "daynight": "D" if i % 2 == 0 else "N",
            "scan": 0.375,
            "track": 0.375,
        }
        for i in range(10)
    ]
    inserted = await repo.bulk_insert_observations(records)
    await async_db_session.commit()
    assert inserted == 10

    # 2. Count
    total = await repo.count()
    assert total == 10

    # 3. Query with filters
    results, count = await repo.query_observations(
        min_frp=20.0,
        satellite="VIIRS_SNPP_NRT",
        limit=5,
        offset=0,
    )
    assert len(results) > 0
    assert count > 0
    for r in results:
        assert r.frp >= 20.0
        assert "SNPP" in r.satellite

    # 4. Spatial bounding box query
    bbox_results, bbox_count = await repo.query_observations(
        bbox=(86.35, 23.70, 86.45, 23.80)
    )
    assert bbox_count > 0

    # 5. Radius query
    nearby = await repo.query_by_radius(latitude=23.76, longitude=86.40, radius_meters=5000)
    assert len(nearby) > 0

    # 6. Summary metrics
    metrics = await repo.get_summary_metrics()
    assert metrics["total_observations"] == 10
    assert metrics["mean_frp_mw"] > 0
    assert metrics["max_frp_mw"] >= 50.0


@pytest.mark.anyio
async def test_thermal_source_repository_crud(async_db_session: AsyncSession):
    repo = ThermalSourceRepository(async_db_session)

    clusters = [
        {
            "cluster_id": 1,
            "centroid_lat": 23.7636,
            "centroid_lon": 86.4008,
            "observation_count": 59,
            "first_seen_utc": datetime(2026, 8, 20, 12, 0),
            "last_seen_utc": datetime(2026, 8, 24, 18, 0),
            "persistence_duration_days": 4.25,
            "mean_frp_mw": 14.5,
            "max_frp_mw": 48.0,
            "mean_brightness_kelvin": 339.0,
            "mean_confidence": 88.0,
            "night_observation_ratio": 0.90,
            "spatial_radius_meters": 450.0,
            "is_persistent": True,
        },
        {
            "cluster_id": 2,
            "centroid_lat": 28.5000,
            "centroid_lon": 77.2000,
            "observation_count": 1,
            "first_seen_utc": datetime(2026, 8, 24, 12, 0),
            "last_seen_utc": datetime(2026, 8, 24, 12, 0),
            "persistence_duration_days": 0.0,
            "mean_frp_mw": 5.0,
            "max_frp_mw": 5.0,
            "mean_brightness_kelvin": 315.0,
            "mean_confidence": 60.0,
            "night_observation_ratio": 0.0,
            "spatial_radius_meters": 0.0,
            "is_persistent": False,
        }
    ]

    inserted = await repo.bulk_upsert_clusters(clusters)
    await async_db_session.commit()
    assert inserted == 2

    # Query persistent only
    persistent_sources, count = await repo.query_sources(persistent_only=True)
    assert count == 1
    assert persistent_sources[0].cluster_id == 1

    # Query by cluster_id
    c1 = await repo.get_by_cluster_id(1)
    assert c1 is not None
    assert c1.observation_count == 59


@pytest.mark.anyio
async def test_classification_repository_crud(async_db_session: AsyncSession):
    repo = ClassificationRepository(async_db_session)

    clf = await repo.create_classification_with_risk(
        classification_data={
            "latitude": 23.76,
            "longitude": 86.40,
            "predicted_class": "persistent_industrial",
            "confidence": 0.95,
            "class_probabilities": {"persistent_industrial": 0.95, "wildfire": 0.05},
            "model_version": "v1.0.0",
        },
        risk_data={
            "risk_score": 82.0,
            "risk_level": "CRITICAL",
            "frp_subscore": 0.70,
            "industrial_proximity_subscore": 0.95,
            "persistence_subscore": 0.90,
            "confidence_subscore": 0.95,
            "nocturnal_subscore": 0.85,
            "reasons": ["Continuous nocturnal thermal emission in industrial corridor"],
        },
    )
    await async_db_session.commit()

    assert clf.id is not None
    assert clf.risk_assessment is not None
    assert clf.risk_assessment.risk_score == 82.0

    # Query by risk level
    results, count = await repo.query_classifications(risk_level="CRITICAL")
    assert count == 1
    assert results[0].predicted_class == "persistent_industrial"


@pytest.mark.anyio
async def test_facility_repository_crud(async_db_session: AsyncSession):
    repo = IndustrialFacilityRepository(async_db_session)

    facilities = [
        {
            "osm_id": 1001,
            "osm_type": "node",
            "name": "Tata Steel Jamshedpur Works",
            "facility_type": "steel_mill",
            "latitude": 22.8046,
            "longitude": 86.2029,
            "tags": {"man_made": "works", "product": "steel"},
        }
    ]
    inserted = await repo.bulk_upsert_facilities(facilities)
    await async_db_session.commit()
    assert inserted == 1

    fac = await repo.get_by_osm_id(1001)
    assert fac is not None
    assert fac.name == "Tata Steel Jamshedpur Works"
