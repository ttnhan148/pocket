"""Variable API endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.variables.schemas import (
    VariableCreate,
    VariableResponse,
    VariableUpdate,
    VariableResolveRequest,
    VariableResolveResponse,
    WorkspaceVariableOverride,
    WorkspaceOverrideRequest,
)
from app.features.variables.service import VariableService

router = APIRouter()


@router.post(
    "",
    response_model=VariableResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new variable definition",
)
async def create_variable(
    data: VariableCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> VariableResponse:
    """Create a new global or workspace-scoped variable definition."""
    service = VariableService(db)
    variable = await service.create_variable(data)
    return VariableResponse.model_validate(variable)


@router.get(
    "",
    response_model=list[VariableResponse],
    summary="List variable definitions",
)
async def list_variables(
    db: Annotated[AsyncSession, Depends(get_session)],
    scope: Annotated[str | None, Query(description="Filter by scope ('global', 'workspace')")] = None,
) -> list[VariableResponse]:
    """Retrieve all variable definitions, optionally filtered by scope."""
    service = VariableService(db)
    variables = await service.list_variables(scope)
    return [VariableResponse.model_validate(v) for v in variables]


@router.get(
    "/{variable_id}",
    response_model=VariableResponse,
    summary="Get variable definition details",
)
async def get_variable(
    variable_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> VariableResponse:
    """Retrieve a variable definition by its ID."""
    service = VariableService(db)
    variable = await service.get_variable(variable_id)
    return VariableResponse.model_validate(variable)


@router.patch(
    "/{variable_id}",
    response_model=VariableResponse,
    summary="Update variable definition",
)
async def update_variable(
    variable_id: str,
    data: VariableUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> VariableResponse:
    """Update editable fields of a variable definition."""
    service = VariableService(db)
    variable = await service.update_variable(variable_id, data)
    return VariableResponse.model_validate(variable)


@router.delete(
    "/{variable_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete variable definition",
)
async def delete_variable(
    variable_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Soft delete a variable definition (if not a system variable)."""
    service = VariableService(db)
    await service.delete_variable(variable_id)


@router.post(
    "/{variable_id}/workspaces/{workspace_id}/override",
    response_model=WorkspaceVariableOverride,
    summary="Override variable value for workspace",
)
async def save_workspace_override(
    variable_id: str,
    workspace_id: str,
    data: WorkspaceOverrideRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> WorkspaceVariableOverride:
    """Save or update a workspace-specific value for a variable definition."""
    service = VariableService(db)
    override = await service.save_workspace_override(workspace_id, variable_id, data.value)
    return WorkspaceVariableOverride.model_validate(override)


@router.post(
    "/resolve",
    response_model=dict[str, VariableResolveResponse],
    summary="Resolve variables",
)
async def resolve_variables(
    data: VariableResolveRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, VariableResolveResponse]:
    """Resolve all variables for a workspace, taking into account priority chain and runtime overrides."""
    service = VariableService(db)
    return await service.resolve_variables(
        workspace_id=data.workspace_id,
        template_vars=data.template_vars,
        runtime_vars=data.runtime_vars,
    )
