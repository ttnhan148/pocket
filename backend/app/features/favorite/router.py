"""API router endpoints for Favorite management."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.favorite.schemas import (
    FavoriteToggleRequest,
    FavoriteResponse,
)
from app.features.favorite.service import FavoriteService

router = APIRouter()


@router.get(
    "",
    response_model=list[FavoriteResponse],
    summary="List all workspace favorites",
)
async def list_favorites(
    workspace_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[FavoriteResponse]:
    """Retrieve all favorited items (contexts, templates, etc.) in the workspace."""
    service = FavoriteService(db)
    favs = await service.list_favorites(workspace_id)
    return [FavoriteResponse.model_validate(f) for f in favs]


@router.post(
    "/toggle",
    response_model=FavoriteResponse | None,
    summary="Toggle favorite status for an entity",
)
async def toggle_favorite(
    workspace_id: str,
    data: FavoriteToggleRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> FavoriteResponse | None:
    """Toggle favoriting of a specific entity (returns the Favorite object if favorited, or None if removed)."""
    service = FavoriteService(db)
    fav = await service.toggle_favorite(workspace_id, data.entity_type, data.entity_id)
    return FavoriteResponse.model_validate(fav) if fav else None


@router.put(
    "/reorder",
    response_model=list[FavoriteResponse],
    summary="Reorder favorites",
)
async def reorder_favorites(
    workspace_id: str,
    ordered_ids: list[str],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[FavoriteResponse]:
    """Update sort order of favorites by supplying the list of favorite UUIDs in preferred order."""
    service = FavoriteService(db)
    favs = await service.reorder_favorites(workspace_id, ordered_ids)
    return [FavoriteResponse.model_validate(f) for f in favs]
