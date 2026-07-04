"""Template API endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.templates.schemas import (
    TemplateCreate,
    TemplateResponse,
    TemplateUpdate,
    TemplateVersionResponse,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
)
from app.features.templates.service import TemplateService

router = APIRouter()


@router.post(
    "",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new template",
)
async def create_template(
    workspace_id: str,
    data: TemplateCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> TemplateResponse:
    """Create a new prompt template and initialize version 1."""
    service = TemplateService(db)
    template = await service.create_template(workspace_id, data)
    return TemplateResponse.model_validate(template)


@router.get(
    "",
    response_model=list[TemplateResponse],
    summary="List templates",
)
async def list_templates(
    workspace_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[TemplateResponse]:
    """Retrieve templates under a workspace, sorted by pinned first."""
    service = TemplateService(db)
    templates = await service.list_templates(workspace_id, skip, limit)
    return [TemplateResponse.model_validate(t) for t in templates]


@router.get(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Get template details",
)
async def get_template(
    workspace_id: str,
    template_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> TemplateResponse:
    """Retrieve details of a prompt template by its ID."""
    service = TemplateService(db)
    template = await service.get_template(workspace_id, template_id)
    return TemplateResponse.model_validate(template)


@router.patch(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Update template",
)
async def update_template(
    workspace_id: str,
    template_id: str,
    data: TemplateUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> TemplateResponse:
    """Update editable fields. Creates a new template version if content or schema changes."""
    service = TemplateService(db)
    template = await service.update_template(workspace_id, template_id, data)
    return TemplateResponse.model_validate(template)


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete template",
)
async def delete_template(
    workspace_id: str,
    template_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Soft delete a prompt template."""
    service = TemplateService(db)
    await service.delete_template(workspace_id, template_id)


@router.get(
    "/{template_id}/versions",
    response_model=list[TemplateVersionResponse],
    summary="Get template version history",
)
async def get_template_versions(
    workspace_id: str,
    template_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[TemplateVersionResponse]:
    """Retrieve version history records for a prompt template."""
    service = TemplateService(db)
    versions = await service.list_versions(workspace_id, template_id)
    return [TemplateVersionResponse.model_validate(v) for v in versions]


@router.post(
    "/{template_id}/preview",
    response_model=TemplatePreviewResponse,
    summary="Preview template rendering",
)
async def preview_template(
    workspace_id: str,
    template_id: str,
    data: TemplatePreviewRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> TemplatePreviewResponse:
    """Render a prompt template preview with resolved variable values and return detected variable list."""
    service = TemplateService(db)
    
    # 1. Detect variables from current template content
    template = await service.get_template(workspace_id, template_id)
    detected = service.detect_variables(template.content)
    
    # 2. Render prompt output
    rendered = await service.render(
        workspace_id=workspace_id,
        template_id=template_id,
        template_vars=data.template_vars,
        runtime_vars=data.runtime_vars,
    )
    
    # 3. Estimate token count of preview
    token_count = service._estimate_token_count(rendered)
    
    return TemplatePreviewResponse(
        rendered=rendered,
        detected_variables=detected,
        token_count=token_count,
    )
