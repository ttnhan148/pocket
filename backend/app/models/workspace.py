"""Workspace models."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Workspace(BaseModel):
    """Workspace represents the top-level organizational unit in Pocket."""

    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # Hex color (e.g. #FFFFFF)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_default: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0 or 1
    metadata_json: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)  # JSON string

    # Relationships
    settings: Mapped[list[WorkspaceSettings]] = relationship(
        "WorkspaceSettings",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )


class WorkspaceSettings(BaseModel):
    """Per-workspace configuration overrides."""

    __tablename__ = "workspace_settings"

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("workspace_id", "key", name="uq_workspace_settings_workspace_key"),
    )

    # Relationships
    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="settings")
