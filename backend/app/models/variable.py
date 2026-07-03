"""Variable models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.template import TemplateVariable


class Variable(BaseModel):
    """Global and workspace-scoped variable definitions."""

    __tablename__ = "variables"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_type: Mapped[str] = mapped_column(String(50), default="text", nullable=False)
    options: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array for select list options
    is_required: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_system: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scope: Mapped[str] = mapped_column(String(50), default="global", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("name", "scope", name="uq_variables_name_scope"),
    )

    # Relationships
    templates: Mapped[list[TemplateVariable]] = relationship("TemplateVariable", back_populates="variable")
    workspace_values: Mapped[list[WorkspaceVariable]] = relationship(
        "WorkspaceVariable",
        back_populates="variable",
        cascade="all, delete-orphan",
    )


class WorkspaceVariable(BaseModel):
    """Variable values scoped to a specific workspace."""

    __tablename__ = "workspace_variables"

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    variable_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("variables.id", ondelete="CASCADE"),
        nullable=False,
    )
    value: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("workspace_id", "variable_id", name="uq_workspace_variables_workspace_variable"),
    )

    # Relationships
    variable: Mapped[Variable] = relationship("Variable", back_populates="workspace_values")
