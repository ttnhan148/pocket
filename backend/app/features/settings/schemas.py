"""Settings schemas for API request and responses."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SettingResponse(BaseModel):
    """Response schema representing a global setting."""

    model_config = ConfigDict(from_attributes=True)

    key: str = Field(..., description="Unique setting key")
    value: str = Field(..., description="Stringified setting value")
    value_type: str = Field(..., description="Type of setting value (boolean, text, number)")
    category: str = Field(..., description="Category of setting (ai, ui, search, etc.)")
    description: str | None = Field(None, description="Optional description of the setting")
    updated_at: datetime


class SettingUpdate(BaseModel):
    """Request schema for updating a single setting."""

    key: str = Field(..., description="The setting key to update")
    value: str = Field(..., description="The new string value")


class SettingBulkUpdateRequest(BaseModel):
    """Request schema for batch updating multiple settings."""

    updates: list[SettingUpdate]
