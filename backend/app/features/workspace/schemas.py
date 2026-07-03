"""Workspace Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceBase(BaseModel):
    """Base fields for Workspace schemas."""

    name: str = Field(..., min_length=1, max_length=255, description="Name of the workspace")
    description: str | None = Field(None, description="Description of the workspace")
    icon: str | None = Field(None, max_length=50, description="Lucide icon name")
    color: str | None = Field(None, max_length=7, description="Hex color value for UI customizability")
    sort_order: int = Field(0, description="Sort order of the workspace in the navigation sidebar")
    metadata_json: dict[str, Any] | None = Field(None, description="Arbitrary JSON metadata")


class WorkspaceCreate(BaseModel):
    """Request schema for creating a new Workspace."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    metadata_json: dict[str, Any] | None = None


class WorkspaceUpdate(BaseModel):
    """Request schema for updating an existing Workspace."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    sort_order: int | None = None
    metadata_json: dict[str, Any] | None = None


class WorkspaceResponse(WorkspaceBase):
    """Response schema for Workspace queries."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID of the workspace")
    slug: str = Field(..., description="URL-safe unique identifier")
    is_default: int = Field(0, description="Whether this is the default workspace (1 = default)")
    created_at: datetime
    updated_at: datetime
