"""Template Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class TemplateBase(BaseModel):
    """Base fields for Prompt Templates."""

    title: str = Field(..., min_length=1, max_length=255, description="Title of the template")
    content: str = Field(..., min_length=1, description="Jinja2 template body")
    description: str | None = None
    template_type: str = Field("prompt", description="prompt | system | partial")
    schema_json: str | None = Field(None, description="JSON Schema for required variables")
    default_variables: str | None = Field(None, description="JSON string of default variable values")
    is_pinned: int = Field(0, ge=0, le=1)
    metadata_json: dict[str, Any] | None = Field(None, description="Arbitrary JSON metadata")


class TemplateCreate(TemplateBase):
    """Request schema for creating a new Template."""
    pass


class TemplateUpdate(BaseModel):
    """Request schema for updating an existing Template."""

    title: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = None
    description: str | None = None
    template_type: str | None = None
    schema_json: str | None = None
    default_variables: str | None = None
    is_pinned: int | None = Field(None, ge=0, le=1)
    metadata_json: dict[str, Any] | None = None
    change_summary: str | None = Field(None, description="Why this version was created")


class TemplateResponse(BaseModel):
    """Response schema for Template queries."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    slug: str
    title: str
    description: str | None
    content: str
    template_type: str
    schema_json: str | None = Field(None, serialization_alias="schema")
    default_variables: str | None
    token_count: int
    usage_count: int
    is_pinned: int
    current_version: int
    metadata_json: dict[str, Any] | None = Field(None, serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime


class TemplateVersionResponse(BaseModel):
    """Response schema for TemplateVersion history queries."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    template_id: str
    version_number: int
    content: str
    schema_json: str | None = Field(None, serialization_alias="schema")
    change_summary: str | None
    created_by: str
    created_at: datetime


class TemplatePreviewRequest(BaseModel):
    """Request schema for previewing template renders."""

    template_vars: dict[str, Any] | None = None
    runtime_vars: dict[str, Any] | None = None


class TemplatePreviewResponse(BaseModel):
    """Response schema for preview rendering."""

    rendered: str
    detected_variables: list[str]
    token_count: int
