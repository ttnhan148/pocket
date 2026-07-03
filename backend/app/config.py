"""Pocket configuration — loads settings from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="POCKET_",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────
    env: str = "development"
    db_path: str = str(Path.home() / ".pocket" / "pocket.db")
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:3000"

    # ── Azure OpenAI ─────────────────────────────────────────────────
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-12-01-preview"
    azure_openai_deployment_chat: str = "gpt-4.1"
    azure_openai_deployment_chat_mini: str = "gpt-4.1-mini"
    azure_openai_deployment_embedding: str = "text-embedding-3-large"

    # ── Embedding ────────────────────────────────────────────────────
    embedding_model_name: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384

    # ── Limits ───────────────────────────────────────────────────────
    token_limit: int = 128_000
    search_top_k: int = 10
    rate_limit_ai: int = 10
    rate_limit_general: int = 100

    # ── Features ─────────────────────────────────────────────────────
    auto_embed: bool = True
    auto_tag: bool = True
    learning_enabled: bool = True
    ai_optimization_enabled: bool = True

    @property
    def database_url(self) -> str:
        """SQLAlchemy database URL."""
        db_path = os.path.expanduser(self.db_path)
        return f"sqlite+aiosqlite:///{db_path}"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
