"""Journal Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class JournalBase(BaseModel):
    """Base fields for Journal."""

    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    mood: str | None = None
    tags: list[str] = Field(default_factory=list)
    is_pinned: int = 0


class JournalCreate(BaseModel):
    """Request schema for creating a Journal entry."""

    workspace_id: str | None = None
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    mood: str | None = None
    tags: list[str] = Field(default_factory=list)


class JournalUpdate(BaseModel):
    """Request schema for updating a Journal entry."""

    title: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = None
    mood: str | None = None
    tags: list[str] | None = None
    is_pinned: int | None = None


class JournalResponse(BaseModel):
    """Response schema for Journal queries."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str | None = None
    title: str
    content: str
    mood: str | None = None
    tags: list[str] = []
    is_pinned: int
    created_at: datetime
    updated_at: datetime
