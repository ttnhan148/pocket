"""Context API endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.context.schemas import (
    ContextCreate,
    ContextResponse,
    ContextUpdate,
    ContextVersionResponse,
)
from app.features.context.service import ContextService

router = APIRouter()


@router.post(
    "",
    response_model=ContextResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new context in a workspace",
)
async def create_context(
    workspace_id: str,
    data: ContextCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ContextResponse:
    """Create a context and generate version 1."""
    service = ContextService(db)
    context = await service.create_context(workspace_id, data)
    return ContextResponse.model_validate(context)


@router.get(
    "",
    response_model=list[ContextResponse],
    summary="List contexts within a workspace",
)
async def list_contexts(
    workspace_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    context_type: Annotated[str | None, Query(description="Filter by context type ('knowledge', 'instruction', 'persona')")] = None,
    is_pinned: Annotated[int | None, Query(ge=0, le=1, description="Filter by pinned (1 = pinned, 0 = not pinned)")] = None,
    is_archived: Annotated[int, Query(ge=0, le=1, description="Filter by archived (1 = archived, 0 = active)")] = 0,
    tag: Annotated[str | None, Query(description="Filter by tag name")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[ContextResponse]:
    """List contexts under a workspace with options to filter by type, pinning, archiving, or tags."""
    service = ContextService(db)
    contexts = await service.list_contexts(
        workspace_id=workspace_id,
        context_type=context_type,
        is_pinned=is_pinned,
        is_archived=is_archived,
        tag_name=tag,
        skip=skip,
        limit=limit,
    )
    return [ContextResponse.model_validate(c) for c in contexts]


@router.get(
    "/search",
    response_model=list[ContextResponse],
    summary="Search contexts using SQLite FTS5",
)
async def search_contexts(
    workspace_id: str,
    q: Annotated[str, Query(min_length=1, description="FTS Search query term")],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[ContextResponse]:
    """Perform full-text search against context title and content fields."""
    service = ContextService(db)
    contexts = await service.search_contexts(workspace_id, q)
    return [ContextResponse.model_validate(c) for c in contexts]


@router.get(
    "/{context_id}",
    response_model=ContextResponse,
    summary="Get context details",
)
async def get_context(
    workspace_id: str,
    context_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ContextResponse:
    """Retrieve details of a context by its ID."""
    service = ContextService(db)
    context = await service.get_context(workspace_id, context_id)
    return ContextResponse.model_validate(context)


@router.put(
    "/{context_id}",
    response_model=ContextResponse,
    summary="Update context",
)
async def update_context(
    workspace_id: str,
    context_id: str,
    data: ContextUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ContextResponse:
    """Update editable fields. Generates a new context version if title/content changes."""
    service = ContextService(db)
    context = await service.update_context(workspace_id, context_id, data)
    return ContextResponse.model_validate(context)


@router.delete(
    "/{context_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete context",
)
async def delete_context(
    workspace_id: str,
    context_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Soft delete context by ID."""
    service = ContextService(db)
    await service.delete_context(workspace_id, context_id)


@router.get(
    "/{context_id}/versions",
    response_model=list[ContextVersionResponse],
    summary="Get context version history",
)
async def get_context_versions(
    workspace_id: str,
    context_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[ContextVersionResponse]:
    """Retrieve version history records for a context, sorted newest first."""
    service = ContextService(db)
    versions = await service.list_versions(workspace_id, context_id)
    return [ContextVersionResponse.model_validate(v) for v in versions]
