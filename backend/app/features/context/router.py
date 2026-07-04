"""Context API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.context.schemas import (
    ContextCreate,
    ContextResponse,
    ContextUpdate,
    ContextVersionResponse,
    ContextGenerateRequest,
    ContextSuggestRequest,
)
from app.features.context.service import ContextService
from app.features.context.ai_service import AIContextService

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


@router.post(
    "/generate",
    response_model=ContextResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new context using AI",
)
async def generate_context(
    workspace_id: str,
    data: ContextGenerateRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ContextResponse:
    """Generate context metadata and markdown contents from a natural language description using LLM."""
    from app.config import Settings
    from app.ai.client import AzureAIClient
    settings = Settings()
    ai_client = AzureAIClient(settings)
    service = AIContextService(db, ai_client, settings)
    context = await service.generate_context(workspace_id, data.description)
    return ContextResponse.model_validate(context)


@router.post(
    "/suggest",
    response_model=list[ContextResponse],
    summary="Suggest semantically relevant contexts for prompt builder",
)
async def suggest_contexts(
    workspace_id: str,
    data: ContextSuggestRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[ContextResponse]:
    """Identify and return active contexts from the workspace that match prompt builder draft text."""
    from app.config import Settings
    from app.ai.client import AzureAIClient
    settings = Settings()
    ai_client = AzureAIClient(settings)
    service = AIContextService(db, ai_client, settings)
    suggestions = await service.suggest_contexts(
        workspace_id,
        data.draft_content,
        data.already_selected_ids,
        data.limit,
    )
    return [ContextResponse.model_validate(s) for s in suggestions]


class ContextHealthResponse(BaseModel):
    """Response schema for context health evaluation."""

    context_id: str
    overall_health: float
    freshness_score: float | None = None
    usage_score: float | None = None
    quality_score: float | None = None
    relevance_score: float | None = None
    issues: list[str] = []
    recommendations: list[str] = []
    evaluated_at: datetime


@router.post(
    "/health-check",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Run AI Context Health Check",
)
async def run_health_check(
    workspace_id: str,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Trigger a background job to scan all contexts and calculate freshness, usage, quality, and relevance."""
    from app.features.jobs.service import AIJobService
    from app.features.jobs.runner import run_context_health_check

    job_service = AIJobService(db)
    job = await job_service.create_job(job_type="health_check", input_data={"workspace_id": workspace_id})
    background_tasks.add_task(run_context_health_check, job.id, workspace_id)
    return {"job_id": job.id, "status": "pending"}


@router.get(
    "/health-scores",
    response_model=list[ContextHealthResponse],
    summary="Get context health scores",
)
async def get_health_scores(
    workspace_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[dict]:
    """Retrieve the latest health scores for all contexts in the workspace."""
    from app.models import Context, ContextHealthScore
    import json

    stmt = (
        select(ContextHealthScore)
        .join(Context, Context.id == ContextHealthScore.context_id)
        .where(Context.workspace_id == workspace_id, Context.deleted_at.is_(None))
        .order_by(ContextHealthScore.evaluated_at.desc())
    )
    res = await db.execute(stmt)
    records = res.scalars().all()

    seen_ctx_ids = set()
    latest_records = []
    for r in records:
        if r.context_id not in seen_ctx_ids:
            seen_ctx_ids.add(r.context_id)
            try:
                issues = json.loads(r.issues) if r.issues else []
            except Exception:
                issues = []
            try:
                recs = json.loads(r.recommendations) if r.recommendations else []
            except Exception:
                recs = []

            latest_records.append({
                "context_id": r.context_id,
                "overall_health": r.overall_health,
                "freshness_score": r.freshness_score,
                "usage_score": r.usage_score,
                "quality_score": r.quality_score,
                "relevance_score": r.relevance_score,
                "issues": issues,
                "recommendations": recs,
                "evaluated_at": r.evaluated_at,
            })

    return latest_records



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





