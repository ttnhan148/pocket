"""Tags and Categories API endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.tags_categories.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryTreeResponse,
    CategoryUpdate,
    TagCreate,
    TagResponse,
    TagUpdate,
)
from app.features.tags_categories.service import CategoryService, TagService

router = APIRouter()


# ── TAGS ENDPOINTS ────────────────────────────────────────────────────────


@router.post(
    "/tags",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tag",
)
async def create_tag(
    workspace_id: str,
    data: TagCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> TagResponse:
    """Create a tag or return existing tag with matching slug."""
    service = TagService(db)
    tag = await service.create_tag(data)
    return TagResponse.model_validate(tag)


@router.get(
    "/tags",
    response_model=list[TagResponse],
    summary="List all active tags",
)
async def list_tags(
    workspace_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[TagResponse]:
    """Retrieve active tags list."""
    service = TagService(db)
    tags = await service.list_tags(skip=skip, limit=limit)
    return [TagResponse.model_validate(t) for t in tags]


@router.get(
    "/tags/{tag_id}",
    response_model=TagResponse,
    summary="Get tag details by ID",
)
async def get_tag(
    workspace_id: str,
    tag_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> TagResponse:
    """Retrieve details of a single tag."""
    service = TagService(db)
    tag = await service.get_tag(tag_id)
    return TagResponse.model_validate(tag)


@router.put(
    "/tags/{tag_id}",
    response_model=TagResponse,
    summary="Update a tag",
)
async def update_tag(
    workspace_id: str,
    tag_id: str,
    data: TagUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> TagResponse:
    """Update editable details of a tag."""
    service = TagService(db)
    tag = await service.update_tag(tag_id, data)
    return TagResponse.model_validate(tag)


@router.delete(
    "/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete a tag",
)
async def delete_tag(
    workspace_id: str,
    tag_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Soft delete tag by ID."""
    service = TagService(db)
    await service.delete_tag(tag_id)


# ── CATEGORIES ENDPOINTS ──────────────────────────────────────────────────


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category folder",
)
async def create_category(
    workspace_id: str,
    data: CategoryCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> CategoryResponse:
    """Create a new category, optionally nested under a parent category."""
    service = CategoryService(db)
    category = await service.create_category(data)
    return CategoryResponse.model_validate(category)


@router.get(
    "/categories",
    response_model=list[CategoryTreeResponse],
    summary="Retrieve categories tree hierarchy",
)
async def get_categories_tree(
    workspace_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[CategoryTreeResponse]:
    """Retrieve the full hierarchical category tree."""
    service = CategoryService(db)
    return await service.get_category_tree()


@router.get(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    summary="Get category details by ID",
)
async def get_category(
    workspace_id: str,
    category_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> CategoryResponse:
    """Retrieve details of a single category."""
    service = CategoryService(db)
    category = await service.get_category(category_id)
    return CategoryResponse.model_validate(category)


@router.put(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    summary="Update a category folder",
)
async def update_category(
    workspace_id: str,
    category_id: str,
    data: CategoryUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> CategoryResponse:
    """Update editable details of a category folder."""
    service = CategoryService(db)
    category = await service.update_category(category_id, data)
    return CategoryResponse.model_validate(category)


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete a category folder",
)
async def delete_category(
    workspace_id: str,
    category_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Soft delete category by ID."""
    service = CategoryService(db)
    await service.delete_category(category_id)
