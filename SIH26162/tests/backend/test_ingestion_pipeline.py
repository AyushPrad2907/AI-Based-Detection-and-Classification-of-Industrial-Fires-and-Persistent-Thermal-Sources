"""
Integration tests for real NASA FIRMS data ingestion into PostgreSQL + PostGIS tables.
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.base import Base
from app.repositories.firms_repository import FIRMSObservationRepository
from app.repositories.thermal_source_repository import ThermalSourceRepository
from ml.utils.data_utils import FIRMSDatasetLoader
from ml.models.thermal_detector import ThermalDetector


@pytest.fixture
async def async_ingest_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.anyio
async def test_bulk_ingestion_from_firms_processed_dataset(async_ingest_session: AsyncSession):
    loader = FIRMSDatasetLoader(data_dir="data/processed/firms")
    df = loader.load_dataset()
    assert len(df) > 0

    detector = ThermalDetector()
    df_clustered, clusters = detector.fit_predict_clusters(df)

    firms_repo = FIRMSObservationRepository(async_ingest_session)
    source_repo = ThermalSourceRepository(async_ingest_session)

    # Ingest observations
    records = []
    for _, row in df_clustered.iterrows():
        rec = {
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "brightness_primary": float(row["brightness_primary"]),
            "brightness_secondary": float(row["brightness_secondary"]) if "brightness_secondary" in row and row["brightness_secondary"] == row["brightness_secondary"] else None,
            "frp": float(row["frp"]),
            "confidence_score": float(row["confidence_score"]),
            "confidence_category": str(row.get("confidence_category", "nominal")),
            "acq_datetime": row["acq_datetime"].to_pydatetime() if hasattr(row["acq_datetime"], "to_pydatetime") else row["acq_datetime"],
            "satellite": str(row.get("satellite", "UNKNOWN")),
            "instrument": str(row.get("instrument", "UNKNOWN")),
            "daynight": str(row.get("daynight", "D")),
            "scan": float(row.get("scan", 0.375)),
            "track": float(row.get("track", 0.375)),
            "source_file": str(row.get("source_file", "")),
            "cluster_id": int(row["cluster_id"]) if row.get("cluster_id") != -1 else None,
        }
        records.append(rec)

    inserted_obs = await firms_repo.bulk_insert_observations(records)
    assert inserted_obs == len(df)

    # Ingest clusters
    cluster_dicts = [
        {
            "cluster_id": c.cluster_id,
            "centroid_lat": c.centroid_lat,
            "centroid_lon": c.centroid_lon,
            "observation_count": c.observation_count,
            "first_seen_utc": c.first_seen,
            "last_seen_utc": c.last_seen,
            "persistence_duration_days": c.duration_days,
            "mean_frp_mw": c.mean_frp,
            "max_frp_mw": c.max_frp,
            "mean_brightness_kelvin": c.mean_brightness,
            "mean_confidence": c.mean_confidence,
            "night_observation_ratio": c.night_ratio,
            "spatial_radius_meters": c.spatial_radius_m,
            "is_persistent": c.is_persistent,
        }
        for c in clusters
    ]
    inserted_clusters = await source_repo.bulk_upsert_clusters(cluster_dicts)
    assert inserted_clusters == len(clusters)

    await async_ingest_session.commit()

    # Query verification
    obs_count = await firms_repo.count()
    sources_count = await source_repo.count()
    assert obs_count == len(df)
    assert sources_count == len(clusters)
