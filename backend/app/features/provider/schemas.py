"""Provider Pydantic validation schemas."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ProviderBase(BaseModel):
    """Base fields for a provider configuration."""

    name: str = Field(..., description="Unique provider configuration name")
    provider_type: str = Field("azure_openai", description="Underlying provider type")
    endpoint: str = Field(..., description="Base API endpoint URL")
    api_version: str = Field(..., description="API version (e.g. 2024-12-01-preview)")
    deployment_chat: str | None = Field(None, description="Azure deployment name for chat completions")
    deployment_chat_mini: str | None = Field(None, description="Azure deployment name for chat-mini model")
    deployment_embedding: str | None = Field(None, description="Azure deployment name for embeddings")
    is_active: int = Field(1, ge=0, le=1, description="Active status (0 = inactive, 1 = active)")


class ProviderCreate(ProviderBase):
    """Schema to create a new provider configuration."""

    api_key: str = Field(..., description="Plain-text API key (will be encrypted on save)")


class ProviderUpdate(BaseModel):
    """Schema to update an existing provider configuration."""

    name: str | None = None
    provider_type: str | None = None
    endpoint: str | None = None
    api_version: str | None = None
    deployment_chat: str | None = None
    deployment_chat_mini: str | None = None
    deployment_embedding: str | None = None
    api_key: str | None = Field(None, description="New plain-text API key (only updated if provided)")
    is_active: int | None = Field(None, ge=0, le=1)


class ProviderResponse(BaseModel):
    """Schema representing provider response (API key is masked)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    provider_type: str
    endpoint: str
    api_version: str
    deployment_chat: str | None
    deployment_chat_mini: str | None
    deployment_embedding: str | None
    is_default: int
    is_active: int
    api_key: str | None = Field("••••••••", description="Masked representation of API key")
    created_at: datetime
    updated_at: datetime


class ProviderTestResponse(BaseModel):
    """Response schema for connection testing."""

    success: bool
    message: str
    latency_ms: float | None = None
