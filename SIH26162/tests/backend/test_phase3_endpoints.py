"""
Integration tests for Phase 3 FastAPI database endpoints and spatial queries.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.core.database import get_db
from app.models.base import Base
from app.models.firms_observation import FIRMSObservation
from app.models.persistent_thermal_source import PersistentThermalSource


@pytest.fixture
async def override_get_db():
    """Overrides FastAPI get_db dependency with an isolated in-memory test database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _test_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _test_get_db
    yield session_factory
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.anyio
async def test_health_and_db_health_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Main health
        res = await client.get("/api/v1/health/")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

        # 2. Database health
        db_res = await client.get("/api/v1/health/db")
        assert db_res.status_code == 200
        assert "status" in db_res.json()
        assert "latency_ms" in db_res.json()


@pytest.mark.anyio
async def test_query_firms_observations_endpoint(override_get_db):
    session_factory = override_get_db

    # Seed observations
    async with session_factory() as session:
        for i in range(5):
            obs = FIRMSObservation(
                latitude=23.76 + i * 0.05,
                longitude=86.40 + i * 0.05,
                brightness_primary=335.0,
                frp=15.0 + i * 10.0,
                confidence_score=80.0,
                confidence_category="nominal",
                acq_datetime=datetime(2026, 8, 24, 12, 0),
                satellite="VIIRS_SNPP_NRT",
                instrument="VIIRS",
            )
            session.add(obs)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Paginated query
        res = await client.get("/api/v1/fires/observations?page=1&limit=10")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 5
        assert len(data["observations"]) == 5

        # Query with FRP filter
        filtered_res = await client.get("/api/v1/fires/observations?min_frp=30.0")
        assert filtered_res.status_code == 200
        assert filtered_res.json()["total"] >= 2

        # Query with Bounding Box filter
        bbox_res = await client.get("/api/v1/fires/observations?bbox=86.30,23.70,86.60,24.00")
        assert bbox_res.status_code == 200
        assert bbox_res.json()["total"] > 0


@pytest.mark.anyio
async def test_classify_and_persist_endpoint(override_get_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "latitude": 23.7636,
            "longitude": 86.4008,
            "brightness_primary": 335.0,
            "brightness_secondary": 295.0,
            "frp": 22.5,
            "confidence": 85.0,
            "daynight": "N",
            "satellite": "VIIRS_SNPP_NRT",
            "instrument": "VIIRS",
            "query_osm": False,
            "persist": True,
        }
        res = await client.post("/api/v1/fires/classify", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["predicted_class"] in [
            "persistent_industrial",
            "industrial_fire",
            "wildfire",
            "agricultural_burn",
            "uncertain_anomaly",
        ]
        assert "risk_score" in data
        assert data["classification_id"] is not None

        # Verify query_stored_classifications endpoint retrieves the persisted record
        clf_query = await client.get("/api/v1/fires/classifications")
        assert clf_query.status_code == 200
        clf_data = clf_query.json()
        assert clf_data["total"] >= 1
        assert clf_data["classifications"][0]["id"] == data["classification_id"]


@pytest.mark.anyio
async def test_thermal_sources_db_integration_endpoint(override_get_db):
    session_factory = override_get_db

    # Seed persistent source
    async with session_factory() as session:
        src = PersistentThermalSource(
            cluster_id=99,
            centroid_lat=23.7636,
            centroid_lon=86.4008,
            observation_count=35,
            first_seen_utc=datetime(2026, 8, 20, 10, 0),
            last_seen_utc=datetime(2026, 8, 24, 18, 0),
            persistence_duration_days=4.33,
            mean_frp_mw=16.8,
            max_frp_mw=42.0,
            mean_brightness_kelvin=337.5,
            mean_confidence=87.0,
            night_observation_ratio=0.88,
            spatial_radius_meters=410.0,
            is_persistent=True,
        )
        session.add(src)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/thermal/sources?min_observations=2&persistent_only=true")
        assert res.status_code == 200
        data = res.json()
        assert data["total_clusters"] >= 1
        assert data["persistent_sources_count"] >= 1
        assert data["clusters"][0]["cluster_id"] == 99
