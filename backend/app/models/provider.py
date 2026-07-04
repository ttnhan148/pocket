"""AI Provider configuration models."""

from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Provider(BaseModel):
    """AI Provider configurations (e.g. Azure OpenAI)."""

    __tablename__ = "providers"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    provider_type: Mapped[str] = mapped_column(String(50), default="azure_openai", nullable=False)
    endpoint: Mapped[str] = mapped_column(String(1024), nullable=False)
    api_version: Mapped[str] = mapped_column(String(50), nullable=False)
    deployment_chat: Mapped[str | None] = mapped_column(String(100), nullable=True)
    deployment_chat_mini: Mapped[str | None] = mapped_column(String(100), nullable=True)
    deployment_embedding: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_default: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)
