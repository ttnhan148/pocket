"""Workspace Repository subclassing BaseRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.models import Workspace


class WorkspaceRepository(BaseRepository[Workspace]):
    """Repository class for database access on Workspace models."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Workspace, db)

    async def get_by_slug(self, slug: str) -> Workspace | None:
        """Fetch workspace by its unique slug."""
        stmt = select(Workspace).where(
            Workspace.slug == slug,
            Workspace.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_default(self) -> Workspace | None:
        """Fetch the default active workspace."""
        stmt = select(Workspace).where(
            Workspace.is_default == 1,
            Workspace.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_ordered(self, skip: int = 0, limit: int = 100) -> list[Workspace]:
        """List active workspaces ordered by sort_order ASC."""
        stmt = (
            select(Workspace)
            .where(Workspace.deleted_at.is_(None))
            .order_by(Workspace.sort_order.asc(), Workspace.name.asc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
