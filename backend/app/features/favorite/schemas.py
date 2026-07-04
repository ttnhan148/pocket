"""Favorite Pydantic validation schemas."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class FavoriteToggleRequest(BaseModel):
    """Request schema to toggle a favorite state on an entity."""

    entity_type: str = Field(..., description="Type of entity: 'context', 'template', or 'conversation'")
    entity_id: str = Field(..., description="The UUID of the entity")


class FavoriteResponse(BaseModel):
    """Response schema for Favorite query."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_type: str
    entity_id: str
    sort_order: int
    created_at: datetime
    updated_at: datetime
