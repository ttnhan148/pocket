"""Journal models."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Journal(BaseModel):
    """Conversation journals for reflection and notes."""

    __tablename__ = "journals"

    workspace_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    mood: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tags_json: Mapped[str | None] = mapped_column("tags", Text, nullable=True)  # JSON array of strings
    is_pinned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
