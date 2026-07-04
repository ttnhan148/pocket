"""Pydantic schemas for variables."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class VariableBase(BaseModel):
    """Base fields for variables."""

    name: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    display_name: str | None = Field(None, max_length=255)
    description: str | None = None
    default_value: str | None = None
    value_type: str = Field("text", description="text | number | boolean | json | select | date")
    options: str | None = Field(None, description="JSON array of select options")
    is_required: int = Field(0, ge=0, le=1)
    is_system: int = Field(0, ge=0, le=1)
    scope: str = Field("global", description="global | workspace")
    sort_order: int = 0


class VariableCreate(VariableBase):
    """Request schema for creating a new Variable."""
    pass


class VariableUpdate(BaseModel):
    """Request schema for updating an existing Variable."""

    display_name: str | None = Field(None, max_length=255)
    description: str | None = None
    default_value: str | None = None
    value_type: str | None = None
    options: str | None = None
    is_required: int | None = Field(None, ge=0, le=1)
    sort_order: int | None = None


class WorkspaceVariableOverride(BaseModel):
    """Request/Response schema for workspace-scoped variable overrides."""

    model_config = ConfigDict(from_attributes=True)

    workspace_id: str
    variable_id: str
    value: str | None = None


class VariableResponse(BaseModel):
    """Response schema for Variable queries."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    display_name: str | None
    description: str | None
    default_value: str | None
    value_type: str
    options: str | None
    is_required: int
    is_system: int
    scope: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class VariableResolveResponse(BaseModel):
    """Response schema for resolved variables."""

    name: str
    value: Any
    value_type: str
    scope: str  # system | global | workspace | template | runtime
    source: str  # Description of where it was resolved from (e.g. "workspace override", "system default")
    is_override: bool


class VariableResolveRequest(BaseModel):
    """Request schema for resolving variables."""

    workspace_id: str
    template_vars: dict[str, Any] | None = None
    runtime_vars: dict[str, Any] | None = None


class WorkspaceOverrideRequest(BaseModel):
    """Request schema for saving variable overrides."""

    value: str | None = None

