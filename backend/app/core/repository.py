"""Generic Repository pattern base class."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.base import BaseModel, utc_now

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Generic repository base providing common CRUD database operations."""

    def __init__(self, model_class: type[ModelType], db: AsyncSession) -> None:
        self.model_class = model_class
        self.db = db

    async def get(self, id_: str) -> ModelType | None:
        """Get a single model instance by its ID."""
        stmt = select(self.model_class).where(
            self.model_class.id == id_,
            self._active_filter(),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_raise(self, id_: str) -> ModelType:
        """Get a single model instance by ID or raise NotFoundError."""
        model = await self.get(id_)
        if model is None:
            raise NotFoundError(self.model_class.__name__, id_)
        return model

    async def list(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """List model instances with pagination, ignoring soft-deleted items."""
        stmt = (
            select(self.model_class)
            .where(self._active_filter())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, model: ModelType) -> ModelType:
        """Add and persist a new model instance."""
        self.db.add(model)
        await self.db.flush()
        return model

    async def update(self, id_: str, data: dict[str, Any]) -> ModelType:
        """Update fields of an existing model instance."""
        model = await self.get_or_raise(id_)
        for key, value in data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        await self.db.flush()
        return model

    async def delete(self, id_: str, soft: bool = True) -> bool:
        """Delete a model instance by ID (supports soft delete if model has deleted_at)."""
        model = await self.get(id_)
        if model is None:
            return False

        if soft:
            model.deleted_at = utc_now()
            await self.db.flush()
        else:
            await self.db.delete(model)
            await self.db.flush()
        return True

    def _active_filter(self) -> Any:
        """SQLAlchemy filter expression to ignore soft deleted records."""
        return self.model_class.deleted_at.is_(None)
