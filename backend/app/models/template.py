"""Template-related models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.variable import Variable


class Template(BaseModel):
    """Jinja2 Prompt Templates."""

    __tablename__ = "templates"

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    template_type: Mapped[str] = mapped_column(String(50), default="prompt", nullable=False)
    schema_json: Mapped[str | None] = mapped_column("schema", Text, nullable=True)  # JSON Schema string
    default_variables: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON values string
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_pinned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    metadata_json: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="uq_templates_workspace_slug"),
    )

    # Relationships
    versions: Mapped[list[TemplateVersion]] = relationship(
        "TemplateVersion",
        back_populates="template",
        cascade="all, delete-orphan",
    )
    variables: Mapped[list[TemplateVariable]] = relationship(
        "TemplateVariable",
        back_populates="template",
        cascade="all, delete-orphan",
    )


class TemplateVersion(BaseModel):
    """Immutable version history for Templates."""

    __tablename__ = "template_versions"

    template_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    schema_json: Mapped[str | None] = mapped_column("schema", Text, nullable=True)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(50), default="user", nullable=False)

    __table_args__ = (
        UniqueConstraint("template_id", "version_number", name="uq_template_versions_id_number"),
    )

    # Relationships
    template: Mapped[Template] = relationship("Template", back_populates="versions")


class TemplateVariable(BaseModel):
    """Junction table linking templates to variables they use."""

    __tablename__ = "template_variables"

    template_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("templates.id", ondelete="CASCADE"),
        primary_key=True,
    )
    variable_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("variables.id", ondelete="CASCADE"),
        primary_key=True,
    )
    is_required: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    default_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    template: Mapped[Template] = relationship("Template", back_populates="variables")
    variable: Mapped[Variable] = relationship("Variable", back_populates="templates")
