"""AI Job Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class AIJobResultResponse(BaseModel):
    """Schema for AI job results."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    result_type: str
    result_data: Any  # Decoded JSON
    entity_type: str | None = None
    entity_id: str | None = None
    applied: int
    created_at: datetime


class AIJobResponse(BaseModel):
    """Schema for AI background jobs."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    job_type: str
    status: str
    progress: float
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    results: list[AIJobResultResponse] = []
