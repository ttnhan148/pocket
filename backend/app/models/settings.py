"""App Settings and Favorites models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BaseModel, utc_now


class Setting(Base):
    """Global application settings stored as key-value pairs."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(50), default="text", nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="general", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class Favorite(BaseModel):
    """User bookmarks for quick access."""

    __tablename__ = "favorites"

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # context | template | conversation | workspace
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", name="uq_favorites_type_id"),
    )
