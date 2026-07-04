"""Journal API router endpoints (M44)."""

from __future__ import annotations

import json
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.journals.service import JournalService
from app.features.journals.schemas import JournalCreate, JournalUpdate, JournalResponse

logger = logging.getLogger("pocket.features.journals.router")

router = APIRouter()


def _map_journal(j) -> dict:
    """Helper to deserialize tags_json database column into tags list."""
    try:
        tags = json.loads(j.tags_json) if j.tags_json else []
    except Exception:
        tags = []

    return {
        "id": j.id,
        "workspace_id": j.workspace_id,
        "title": j.title,
        "content": j.content,
        "mood": j.mood,
        "tags": tags,
        "is_pinned": j.is_pinned,
        "created_at": j.created_at,
        "updated_at": j.updated_at,
    }


@router.post(
    "",
    response_model=JournalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new journal entry",
)
async def create_journal(
    data: JournalCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Create a workspace journal entry with tags and mood indicators."""
    service = JournalService(db)
    journal = await service.create_journal(data)
    return _map_journal(journal)


@router.get(
    "",
    response_model=list[JournalResponse],
    summary="List workspace journals",
)
async def list_journals(
    workspace_id: Annotated[str | None, Query(description="Filter by workspace")] = None,
    q: Annotated[str | None, Query(description="Full text search query term")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    db: Annotated[AsyncSession, Depends(get_session)] = None,
) -> list[dict]:
    """Retrieve lists of journal entries with FTS search capabilities."""
    service = JournalService(db)
    journals = await service.list_journals(workspace_id=workspace_id, query=q, skip=skip, limit=limit)
    return [_map_journal(j) for j in journals]


@router.get(
    "/{journal_id}",
    response_model=JournalResponse,
    summary="Get journal entry details",
)
async def get_journal(
    journal_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Retrieve details of a single journal entry."""
    service = JournalService(db)
    journal = await service.get_journal(journal_id)
    return _map_journal(journal)


@router.put(
    "/{journal_id}",
    response_model=JournalResponse,
    summary="Update journal entry",
)
async def update_journal(
    journal_id: str,
    data: JournalUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Modify editable details of a journal entry, including pinning states and tags."""
    service = JournalService(db)
    journal = await service.update_journal(journal_id, data)
    return _map_journal(journal)


@router.delete(
    "/{journal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete journal entry",
)
async def delete_journal(
    journal_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Soft delete a journal entry by ID."""
    service = JournalService(db)
    await service.delete_journal(journal_id)
