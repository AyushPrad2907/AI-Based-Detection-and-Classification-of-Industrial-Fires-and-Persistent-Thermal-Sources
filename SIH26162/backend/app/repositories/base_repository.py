"""
SIH26162 — Base Async Repository.

Provides standard asynchronous CRUD operations for SQLAlchemy models.
"""

from typing import Any, Generic, List, Optional, Sequence, Type, TypeVar
from sqlalchemy import func, select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async CRUD repository."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id_val: Any) -> Optional[ModelType]:
        """Fetch a single record by primary key."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id_val)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ModelType]:
        """Fetch records with pagination."""
        query = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count(self) -> int:
        """Count total records in table."""
        query = select(func.count()).select_from(self.model)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def create(self, **kwargs) -> ModelType:
        """Create and insert a single record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def delete_by_id(self, id_val: Any) -> bool:
        """Delete a record by primary key."""
        stmt = delete(self.model).where(self.model.id == id_val)
        res = await self.session.execute(stmt)
        return res.rowcount > 0
