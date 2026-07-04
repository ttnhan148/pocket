"""Pydantic schemas for Conversation and Message models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class MessageBase(BaseModel):
    role: str  # system | user | assistant
    content: str


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    content: str
    token_count: int
    model: Optional[str] = None
    latency_ms: Optional[int] = None
    cost: float
    finish_reason: Optional[str] = None
    metadata_json: Optional[str] = None  # JSON string
    created_at: datetime


class ConversationBase(BaseModel):
    title: str
    model: str


class ConversationCreate(BaseModel):
    workspace_id: str
    title: str
    model: str
    provider_id: Optional[str] = None
    system_prompt: Optional[str] = None


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[int] = None
    is_archived: Optional[int] = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    provider_id: Optional[str] = None
    title: str
    summary: Optional[str] = None
    model: str
    system_prompt: Optional[str] = None
    total_tokens: int
    total_cost: float
    message_count: int
    is_pinned: int
    is_archived: int
    metadata_json: Optional[str] = None  # JSON string
    started_at: datetime
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
