"""Context Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.features.tags_categories.schemas import TagResponse


class ContextBase(BaseModel):
    """Base fields for Context schemas."""

    title: str = Field(..., min_length=1, max_length=255, description="Title of the context")
    content: str = Field(..., min_length=1, description="The markdown text content of the context")
    context_type: str = Field(..., description="Type of context: 'knowledge', 'instruction', or 'persona'")
    priority: int = Field(50, ge=0, le=100, description="Relative priority / rank (0-100)")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence score of context contents (0.0 - 1.0)")
    is_pinned: int = Field(0, description="Whether the context is pinned (1 = pinned, 0 = normal)")
    is_archived: int = Field(0, description="Whether the context is archived (1 = archived, 0 = active)")
    metadata_json: dict[str, Any] | None = Field(None, description="Arbitrary JSON metadata")


class ContextCreate(BaseModel):
    """Request schema for creating a new Context."""

    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    context_type: str = Field("knowledge", description="'knowledge', 'instruction', or 'persona'")
    priority: int = 50
    confidence: float = 1.0
    metadata_json: dict[str, Any] | None = None
    category_id: str | None = None
    tag_ids: list[str] | None = None


class ContextUpdate(BaseModel):
    """Request schema for updating an existing Context."""

    title: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = None
    priority: int | None = Field(None, ge=0, le=100)
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    is_pinned: int | None = None
    is_archived: int | None = None
    metadata_json: dict[str, Any] | None = None
    category_id: str | None = None
    tag_ids: list[str] | None = None


class ContextResponse(BaseModel):
    """Response schema for Context queries."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    slug: str
    title: str
    content: str
    context_type: str
    priority: int
    confidence: float
    token_count: int
    usage_count: int
    last_used_at: str | None
    is_pinned: int
    is_archived: int
    current_version: int
    metadata_json: dict[str, Any] | None
    category_id: str | None = None
    tags: list[TagResponse] = []
    created_at: datetime
    updated_at: datetime


class ContextVersionResponse(BaseModel):
    """Response schema for ContextVersion queries."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    context_id: str
    version_number: int
    title: str
    content: str
    created_at: datetime
