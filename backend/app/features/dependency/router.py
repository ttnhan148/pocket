"""API router endpoints for Context Dependency Graph (DAG) management."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.dependency.schemas import (
    DependencyCreate,
    DependencyGraphResponse,
    DependencyResponse,
)
from app.features.dependency.service import DependencyService

router = APIRouter()


@router.post(
    "/contexts/{context_id}/dependencies",
    response_model=DependencyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add context dependency relationship",
)
async def add_dependency(
    workspace_id: str,
    context_id: str,
    data: DependencyCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> DependencyResponse:
    """Establish a dependency edge where context_id depends on target_id."""
    service = DependencyService(db)
    dep = await service.add_dependency(workspace_id, context_id, data)
    return DependencyResponse.model_validate(dep)


@router.delete(
    "/contexts/{context_id}/dependencies/{target_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove context dependency relationship",
)
async def remove_dependency(
    workspace_id: str,
    context_id: str,
    target_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Delete a dependency edge relationship."""
    service = DependencyService(db)
    await service.remove_dependency(workspace_id, context_id, target_id)


@router.get(
    "/dependency-graph",
    response_model=DependencyGraphResponse,
    summary="Get entire workspace context dependency DAG",
)
async def get_dependency_graph(
    workspace_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> DependencyGraphResponse:
    """Retrieve all context nodes and directed edges sorted topologically."""
    service = DependencyService(db)
    return await service.get_graph(workspace_id)
