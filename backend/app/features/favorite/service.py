"""Business logic service for Favorites."""

from __future__ import annotations

from typing import Any
from sqlalchemy import select

from app.core.exceptions import NotFoundError, ValidationError
from app.core.service import BaseService
from app.features.favorite.repository import FavoriteRepository
from app.models import Favorite, Context, Template, Conversation


class FavoriteService(BaseService):
    """Manages favorited entities (contexts, templates, conversations) for a workspace."""

    def __init__(self, db: Any) -> None:
        super().__init__(db)
        self.repo = FavoriteRepository(db)

    async def list_favorites(self, workspace_id: str) -> list[Favorite]:
        """List all favorites belonging to entities in the specified workspace."""
        return await self.repo.list_by_workspace(workspace_id)

    async def toggle_favorite(self, workspace_id: str, entity_type: str, entity_id: str) -> Favorite | None:
        """Toggle favorite state of an entity. Returns the Favorite model if added, or None if removed."""
        # 1. Enforce entity exists and belongs to the workspace
        if entity_type == "context":
            stmt = select(Context).where(
                Context.id == entity_id,
                Context.workspace_id == workspace_id,
                Context.deleted_at.is_(None)
            )
            res = await self.db.execute(stmt)
            if not res.scalar_one_or_none():
                raise NotFoundError("Context", entity_id)
        elif entity_type == "template":
            stmt = select(Template).where(
                Template.id == entity_id,
                Template.workspace_id == workspace_id,
                Template.deleted_at.is_(None)
            )
            res = await self.db.execute(stmt)
            if not res.scalar_one_or_none():
                raise NotFoundError("Template", entity_id)
        elif entity_type == "conversation":
            stmt = select(Conversation).where(
                Conversation.id == entity_id,
                Conversation.workspace_id == workspace_id,
                Conversation.deleted_at.is_(None)
            )
            res = await self.db.execute(stmt)
            if not res.scalar_one_or_none():
                raise NotFoundError("Conversation", entity_id)
        else:
            raise ValidationError(f"Invalid entity type: {entity_type}")

        # 2. Check if already favorited
        fav = await self.repo.get_by_entity(entity_type, entity_id)
        if fav:
            # Toggle off: delete the favorite record
            await self.db.delete(fav)
            await self.db.flush()
            return None
        else:
            # Toggle on: create new favorite record
            max_stmt = select(Favorite.sort_order).order_by(Favorite.sort_order.desc()).limit(1)
            max_res = await self.db.execute(max_stmt)
            max_val = max_res.scalar_one_or_none() or 0

            fav = Favorite(
                entity_type=entity_type,
                entity_id=entity_id,
                sort_order=max_val + 1
            )
            self.db.add(fav)
            await self.db.flush()
            return fav

    async def reorder_favorites(self, workspace_id: str, ordered_ids: list[str]) -> list[Favorite]:
        """Update the sort order of favorites in the workspace."""
        favs = await self.repo.list_by_workspace(workspace_id)
        fav_map = {f.id: f for f in favs}

        updated = []
        for idx, fid in enumerate(ordered_ids):
            if fid in fav_map:
                fav = fav_map[fid]
                fav.sort_order = idx
                updated.append(fav)
        await self.db.flush()
        return updated
