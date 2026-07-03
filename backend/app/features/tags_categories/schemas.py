"""Tags and Categories Pydantic validation schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TagBase(BaseModel):
    """Base fields for Tag schemas."""

    name: str = Field(..., min_length=1, max_length=255)
    color: str | None = Field(None, max_length=7)


class TagCreate(TagBase):
    """Request schema for creating a new Tag."""



class TagUpdate(BaseModel):
    """Request schema for updating an existing Tag's details."""

    name: str | None = Field(None, min_length=1, max_length=255)
    color: str | None = Field(None, max_length=7)


class TagResponse(TagBase):
    """Response schema for Tag queries."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    usage_count: int
    created_at: datetime
    updated_at: datetime


class CategoryBase(BaseModel):
    """Base fields for Category schemas."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    icon: str | None = Field(None, max_length=50)
    color: str | None = Field(None, max_length=7)
    sort_order: int = 0
    parent_id: str | None = None


class CategoryCreate(CategoryBase):
    """Request schema for creating a new Category."""



class CategoryUpdate(BaseModel):
    """Request schema for updating an existing Category."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    icon: str | None = Field(None, max_length=50)
    color: str | None = Field(None, max_length=7)
    sort_order: int | None = None
    parent_id: str | None = None


class CategoryResponse(CategoryBase):
    """Response schema for Category details."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    created_at: datetime
    updated_at: datetime


class CategoryTreeResponse(CategoryResponse):
    """Hierarchical category tree response schema."""

    children: list[CategoryTreeResponse] = []


CategoryTreeResponse.model_rebuild()
