"""Favorite Repository subclassing BaseRepository."""

from __future__ import annotations

from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.models import Favorite, Context, Template, Conversation


class FavoriteRepository(BaseRepository[Favorite]):
    """Repository class for database access on Favorite models."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Favorite, db)

    async def get_by_entity(self, entity_type: str, entity_id: str) -> Favorite | None:
        """Fetch favorite record by entity type and ID."""
        stmt = select(Favorite).where(
            Favorite.entity_type == entity_type,
            Favorite.entity_id == entity_id,
            Favorite.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_by_workspace(self, workspace_id: str) -> list[Favorite]:
        """Fetch all favorites belonging to entities in the specified workspace, ordered by sort_order."""
        # Subqueries to retrieve active entity IDs for the workspace
        context_sub = select(Context.id).where(
            Context.workspace_id == workspace_id,
            Context.deleted_at.is_(None)
        )
        template_sub = select(Template.id).where(
            Template.workspace_id == workspace_id,
            Template.deleted_at.is_(None)
        )
        conv_sub = select(Conversation.id).where(
            Conversation.workspace_id == workspace_id,
            Conversation.deleted_at.is_(None)
        )

        stmt = select(Favorite).where(
            Favorite.deleted_at.is_(None),
            or_(
                and_(Favorite.entity_type == "context", Favorite.entity_id.in_(context_sub)),
                and_(Favorite.entity_type == "template", Favorite.entity_id.in_(template_sub)),
                and_(Favorite.entity_type == "conversation", Favorite.entity_id.in_(conv_sub)),
            )
        ).order_by(Favorite.sort_order.asc(), Favorite.created_at.desc())

        res = await self.db.execute(stmt)
        return list(res.scalars().all())
