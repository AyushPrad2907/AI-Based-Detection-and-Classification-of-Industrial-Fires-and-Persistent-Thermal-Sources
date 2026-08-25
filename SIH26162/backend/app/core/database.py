"""
SIH26162 — PostgreSQL + PostGIS Async Database Engine & Session Management.

Provides the async SQLAlchemy 2.0 engine, scoped session factory, dependency injection,
and health diagnostic probes for PostgreSQL + PostGIS.
"""

import logging
import time
from typing import AsyncGenerator, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.models.base import Base

logger = logging.getLogger("database")

# ---------------------------------------------------------------------------
# Async Engine & Session Factory Setup
# ---------------------------------------------------------------------------
def create_engine_and_session(
    database_url: Optional[str] = None,
    echo: Optional[bool] = None,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create a configured async SQLAlchemy engine and session factory."""
    url = database_url or settings.async_database_url
    is_debug = settings.debug if echo is None else echo

    # Engine arguments
    engine_kwargs: Dict[str, Any] = {
        "echo": is_debug,
        "future": True,
    }

    # Connection pooling for PostgreSQL (asyncpg)
    if "postgresql" in url:
        engine_kwargs.update({
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "pool_timeout": 30.0,
        })

    engine = create_async_engine(url, **engine_kwargs)
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    return engine, session_factory


# Global engine and session factory
engine, async_session = create_engine_and_session()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an async database session.
    Commits upon normal completion; rolls back automatically on error;
    ensures session is closed cleanly upon exit.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as err:
            await session.rollback()
            logger.error(f"Database session error (transaction rolled back): {err}")
            raise


async def init_db(target_engine: Optional[AsyncEngine] = None) -> None:
    """
    Initialize database schema (creates tables if not exist).
    In production, Alembic migrations should be used.
    """
    eng = target_engine or engine
    async with eng.begin() as conn:
        if "postgresql" in str(eng.url):
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                logger.info("PostGIS extension ensured.")
            except Exception as e:
                logger.warning(f"Could not enable PostGIS extension automatically: {e}")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")


async def check_database_health() -> Dict[str, Any]:
    """
    Probe the database for connectivity, PostGIS extension status, and record statistics.
    """
    start_time = time.perf_counter()
    try:
        async with async_session() as session:
            # Check basic connection
            res = await session.execute(text("SELECT 1;"))
            res.scalar()

            # Check PostGIS extension
            postgis_version = None
            try:
                pg_res = await session.execute(text("SELECT PostGIS_Full_Version();"))
                postgis_version = pg_res.scalar()
            except Exception:
                postgis_version = "Not available or not installed"

            # Check table counts
            counts = {}
            for table_name in [
                "firms_observations",
                "persistent_thermal_sources",
                "thermal_classifications",
                "risk_assessments",
                "industrial_facilities",
            ]:
                try:
                    c_res = await session.execute(text(f"SELECT count(*) FROM {table_name};"))
                    counts[table_name] = c_res.scalar() or 0
                except Exception:
                    counts[table_name] = "Table does not exist"

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            return {
                "status": "connected",
                "healthy": True,
                "latency_ms": latency_ms,
                "database_url": settings.async_database_url.split("@")[-1] if "@" in settings.async_database_url else "configured",
                "postgis_version": postgis_version,
                "record_counts": counts,
            }

    except Exception as err:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.warning(f"Database health check failed: {err}")
        return {
            "status": "disconnected",
            "healthy": False,
            "latency_ms": latency_ms,
            "error": str(err),
            "database_url": settings.async_database_url.split("@")[-1] if "@" in settings.async_database_url else "configured",
            "postgis_version": None,
            "record_counts": {},
        }
