"""Workspace API endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.workspace.schemas import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
from app.features.workspace.service import WorkspaceService

router = APIRouter()


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workspace",
)
async def create_workspace(
    data: WorkspaceCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> WorkspaceResponse:
    """Create a new workspace with a unique slug and return details."""
    service = WorkspaceService(db)
    workspace = await service.create_workspace(data)
    return WorkspaceResponse.model_validate(workspace)


@router.get(
    "",
    response_model=list[WorkspaceResponse],
    summary="List all active workspaces",
)
async def list_workspaces(
    db: Annotated[AsyncSession, Depends(get_session)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[WorkspaceResponse]:
    """Retrieve all workspaces ordered by sort_order ASC."""
    service = WorkspaceService(db)
    workspaces = await service.list_workspaces(skip=skip, limit=limit)
    return [WorkspaceResponse.model_validate(w) for w in workspaces]


@router.get(
    "/default",
    response_model=WorkspaceResponse,
    summary="Get the default active workspace",
)
async def get_default_workspace(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> WorkspaceResponse:
    """Retrieve the default workspace."""
    service = WorkspaceService(db)
    workspace = await service.repo.get_default()
    if not workspace:
        # Fallback: check if any workspace exists and return first
        workspaces = await service.list_workspaces(limit=1)
        if workspaces:
            workspace = workspaces[0]
            await service.set_default_workspace(workspace.id)
        else:
            # Create a default workspace automatically
            default_data = WorkspaceCreate(
                name="Default Workspace",
                description="Default system workspace",
            )
            workspace = await service.create_workspace(default_data)
            await service.set_default_workspace(workspace.id)

    return WorkspaceResponse.model_validate(workspace)


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Get workspace details by ID",
)
async def get_workspace(
    workspace_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> WorkspaceResponse:
    """Retrieve a single workspace by ID."""
    service = WorkspaceService(db)
    workspace = await service.get_workspace(workspace_id)
    return WorkspaceResponse.model_validate(workspace)


@router.put(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Update an existing workspace",
)
async def update_workspace(
    workspace_id: str,
    data: WorkspaceUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> WorkspaceResponse:
    """Update editable fields of a workspace."""
    service = WorkspaceService(db)
    workspace = await service.update_workspace(workspace_id, data)
    return WorkspaceResponse.model_validate(workspace)


@router.put(
    "/{workspace_id}/default",
    response_model=WorkspaceResponse,
    summary="Set workspace as default active",
)
async def set_default_workspace(
    workspace_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> WorkspaceResponse:
    """Mark a workspace as default and reset previous defaults."""
    service = WorkspaceService(db)
    workspace = await service.set_default_workspace(workspace_id)
    return WorkspaceResponse.model_validate(workspace)


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a workspace",
)
async def delete_workspace(
    workspace_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Soft delete a workspace (cannot delete default workspace)."""
    service = WorkspaceService(db)
    await service.delete_workspace(workspace_id)
