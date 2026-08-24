"""
Unit tests for SQLAlchemy ORM models, relationships, and constraints.
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.base import Base
from app.models.firms_observation import FIRMSObservation
from app.models.persistent_thermal_source import PersistentThermalSource
from app.models.classification import ThermalClassification
from app.models.risk_assessment import RiskAssessment
from app.models.industrial_facility import IndustrialFacility
from app.models.model_metadata import MLModelMetadata


@pytest.fixture
async def async_test_session():
    """Provides an isolated in-memory async SQLite database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.anyio
async def test_firms_observation_model(async_test_session: AsyncSession):
    obs = FIRMSObservation(
        latitude=23.7636,
        longitude=86.4008,
        brightness_primary=335.5,
        brightness_secondary=298.0,
        frp=12.5,
        confidence_score=85.0,
        confidence_category="high",
        acq_datetime=datetime(2026, 8, 24, 14, 30),
        satellite="VIIRS_SNPP_NRT",
        instrument="VIIRS",
        daynight="D",
        scan=0.375,
        track=0.375,
    )
    async_test_session.add(obs)
    await async_test_session.commit()

    assert obs.id is not None
    assert "FIRMSObservation" in repr(obs)
    assert obs.latitude == 23.7636
    assert obs.created_at is not None


@pytest.mark.anyio
async def test_classification_and_risk_assessment_relationship(async_test_session: AsyncSession):
    obs = FIRMSObservation(
        latitude=15.1771,
        longitude=76.6684,
        brightness_primary=340.0,
        frp=25.0,
        confidence_score=90.0,
        confidence_category="high",
        acq_datetime=datetime(2026, 8, 24, 18, 0),
        satellite="VIIRS_NOAA20_NRT",
        instrument="VIIRS",
    )
    async_test_session.add(obs)
    await async_test_session.flush()

    clf = ThermalClassification(
        observation_id=obs.id,
        latitude=obs.latitude,
        longitude=obs.longitude,
        predicted_class="persistent_industrial",
        confidence=0.98,
        class_probabilities={"persistent_industrial": 0.98, "wildfire": 0.02},
        model_version="v1.0.0",
    )
    async_test_session.add(clf)
    await async_test_session.flush()

    risk = RiskAssessment(
        classification_id=clf.id,
        observation_id=obs.id,
        risk_score=78.5,
        risk_level="CRITICAL",
        frp_subscore=0.65,
        industrial_proximity_subscore=0.90,
        persistence_subscore=0.95,
        confidence_subscore=0.90,
        nocturnal_subscore=0.85,
        reasons=["High persistence", "Industrial proximity"],
    )
    async_test_session.add(risk)
    await async_test_session.commit()

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    res = await async_test_session.execute(
        select(ThermalClassification)
        .options(selectinload(ThermalClassification.risk_assessment))
        .where(ThermalClassification.id == clf.id)
    )
    loaded_clf = res.scalar_one()

    assert loaded_clf.risk_assessment is not None
    assert loaded_clf.risk_assessment.risk_level == "CRITICAL"
    assert "RiskAssessment" in repr(risk)


@pytest.mark.anyio
async def test_persistent_thermal_source_and_facility_relationship(async_test_session: AsyncSession):
    facility = IndustrialFacility(
        osm_id=987654321,
        osm_type="way",
        name="Bokaro Steel Works",
        facility_type="steel_mill",
        latitude=23.6810,
        longitude=86.3960,
        tags={"industrial": "metallurgy", "operator": "SAIL"},
    )
    async_test_session.add(facility)
    await async_test_session.flush()

    source = PersistentThermalSource(
        cluster_id=42,
        centroid_lat=23.6815,
        centroid_lon=86.3965,
        observation_count=25,
        first_seen_utc=datetime(2026, 8, 20, 10, 0),
        last_seen_utc=datetime(2026, 8, 24, 18, 0),
        persistence_duration_days=4.33,
        mean_frp_mw=18.4,
        max_frp_mw=45.2,
        mean_brightness_kelvin=338.2,
        mean_confidence=88.5,
        night_observation_ratio=0.84,
        spatial_radius_meters=350.0,
        is_persistent=True,
        nearest_industrial_facility_id=facility.id,
    )
    async_test_session.add(source)
    await async_test_session.commit()

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    res = await async_test_session.execute(
        select(PersistentThermalSource)
        .options(selectinload(PersistentThermalSource.nearest_facility))
        .where(PersistentThermalSource.id == source.id)
    )
    loaded_source = res.scalar_one()

    assert loaded_source.id is not None
    assert loaded_source.nearest_facility.name == "Bokaro Steel Works"
    assert "PersistentThermalSource" in repr(source)
    assert "IndustrialFacility" in repr(facility)


@pytest.mark.anyio
async def test_model_metadata_model(async_test_session: AsyncSession):
    meta = MLModelMetadata(
        model_name="FireClassifier_Ensemble",
        model_type="random_forest",
        version="v1.0.0",
        dataset_size=1865,
        train_accuracy=1.0,
        test_accuracy=0.9821,
        test_f1_macro=0.9795,
        test_roc_auc=0.9996,
        features_used=["persistence_count", "frp", "brightness_diff"],
        artifact_path="ml/saved_models/fire_classifier.joblib",
        is_active=True,
    )
    async_test_session.add(meta)
    await async_test_session.commit()

    assert meta.id is not None
    assert "MLModelMetadata" in repr(meta)
