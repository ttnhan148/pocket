"""Template Repository subclassing BaseRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.models import Template, TemplateVersion


class TemplateRepository(BaseRepository[Template]):
    """Repository class for database access on Template models."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Template, db)

    async def get_by_slug(self, workspace_id: str, slug: str) -> Template | None:
        """Fetch template by workspace ID and slug, ignoring soft-deleted items."""
        stmt = (
            select(Template)
            .where(
                Template.workspace_id == workspace_id,
                Template.slug == slug,
                Template.deleted_at.is_(None),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_by_workspace(
        self,
        workspace_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Template]:
        """List templates under a workspace, sorted by pinned and updated date."""
        stmt = (
            select(Template)
            .where(
                Template.workspace_id == workspace_id,
                Template.deleted_at.is_(None),
            )
            .order_by(Template.is_pinned.desc(), Template.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def list_versions(self, template_id: str) -> list[TemplateVersion]:
        """List all version history records for a template."""
        stmt = (
            select(TemplateVersion)
            .where(TemplateVersion.template_id == template_id)
            .order_by(TemplateVersion.version_number.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
