"""Tags and Categories database repositories."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.models import Category, Tag


class TagRepository(BaseRepository[Tag]):
    """Repository class for Tag database access."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Tag, db)

    async def get_by_slug(self, slug: str) -> Tag | None:
        """Fetch tag by slug."""
        stmt = select(Tag).where(Tag.slug == slug, Tag.deleted_at.is_(None))
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Tag | None:
        """Fetch tag by exact name."""
        stmt = select(Tag).where(Tag.name == name, Tag.deleted_at.is_(None))
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()


class CategoryRepository(BaseRepository[Category]):
    """Repository class for Category database access."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Category, db)

    async def get_by_slug(self, slug: str) -> Category | None:
        """Fetch category by slug."""
        stmt = select(Category).where(Category.slug == slug, Category.deleted_at.is_(None))
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_roots(self) -> list[Category]:
        """Fetch all top-level category tree roots (no parent)."""
        stmt = select(Category).where(
            Category.parent_id.is_(None),
            Category.deleted_at.is_(None),
        ).order_by(Category.sort_order.asc(), Category.name.asc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def list_children(self, parent_id: str) -> list[Category]:
        """Fetch immediate sub-categories of parent."""
        stmt = select(Category).where(
            Category.parent_id == parent_id,
            Category.deleted_at.is_(None),
        ).order_by(Category.sort_order.asc(), Category.name.asc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
