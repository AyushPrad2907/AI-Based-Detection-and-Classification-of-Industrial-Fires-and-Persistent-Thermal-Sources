"""
SIH26162 — Database Configuration (Placeholder).

Sets up the async SQLAlchemy engine and session for PostgreSQL + PostGIS.
This will be fully implemented in Phase 3 when database tables are defined.

Usage (when implemented):
    from app.core.database import get_db

    @router.get("/")
    async def endpoint(db: AsyncSession = Depends(get_db)):
        ...
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import settings

# ---------------------------------------------------------------------------
# Async Engine Setup
# ---------------------------------------------------------------------------
# The engine connects to PostgreSQL with the PostGIS extension.
# Ensure PostGIS is installed: CREATE EXTENSION IF NOT EXISTS postgis;
# ---------------------------------------------------------------------------
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """
    Dependency that provides an async database session.

    Usage in endpoints:
        db: AsyncSession = Depends(get_db)
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
