"""Context Repository subclassing BaseRepository."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.models import Context


class ContextRepository(BaseRepository[Context]):
    """Repository class for database access on Context models."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Context, db)

    async def get_by_slug(self, workspace_id: str, slug: str) -> Context | None:
        """Fetch a context by workspace and slug."""
        stmt = select(Context).where(
            Context.workspace_id == workspace_id,
            Context.slug == slug,
            Context.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_by_workspace(
        self,
        workspace_id: str,
        context_type: str | None = None,
        is_pinned: int | None = None,
        is_archived: int = 0,
        tag_name: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Context]:
        """List contexts inside a workspace with optional filters."""
        stmt = select(Context).where(
            Context.workspace_id == workspace_id,
            Context.deleted_at.is_(None),
        )

        if context_type:
            stmt = stmt.where(Context.context_type == context_type)
        if is_pinned is not None:
            stmt = stmt.where(Context.is_pinned == is_pinned)
        if is_archived is not None:
            stmt = stmt.where(Context.is_archived == is_archived)

        if tag_name:
            # Join with tags secondary table
            stmt = stmt.join(Context.tags).where(sa.func.lower(sa.text("tags.name")) == tag_name.lower())

        stmt = stmt.order_by(Context.is_pinned.desc(), Context.updated_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def search(self, workspace_id: str, query_string: str) -> list[Context]:
        """Search contexts in a workspace using SQLite FTS5 matching."""
        if not query_string.strip():
            return []

        # SQLite FTS5 search query
        stmt = sa.text(
            """
            SELECT c.id FROM contexts c
            JOIN contexts_fts fts ON c.rowid = fts.rowid
            WHERE c.workspace_id = :workspace_id
              AND c.deleted_at IS NULL
              AND contexts_fts MATCH :query
            """
        )
        # Escape double quotes and wrap query in double quotes for FTS5 matching
        clean_query = query_string.replace('"', '""')
        escaped_query = f'"{clean_query}"'

        res = await self.db.execute(
            stmt,
            {"workspace_id": workspace_id, "query": escaped_query},
        )
        ids = [row[0] for row in res.fetchall()]
        if not ids:
            return []

        # Load contexts by IDs
        load_stmt = select(Context).where(Context.id.in_(ids))
        load_res = await self.db.execute(load_stmt)
        return list(load_res.scalars().all())
