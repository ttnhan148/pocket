"""Context-related models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, utc_now

# Many-to-many junction table for contexts <-> tags
context_tags = Table(
    "context_tags",
    BaseModel.metadata,
    Column("context_id", String(36), ForeignKey("contexts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(36), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", String, default=lambda: datetime.now(UTC).isoformat() + "Z"),
)


class Category(BaseModel):
    """Category represents a hierarchical categorization for contexts."""

    __tablename__ = "categories"

    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    parent: Mapped[Category | None] = relationship("Category", remote_side="Category.id", backref="children")
    contexts: Mapped[list[Context]] = relationship("Context", back_populates="category")


class Tag(BaseModel):
    """Tag registry for tagging contexts."""

    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Context(BaseModel):
    """Context represents a first-class Knowledge Object."""

    __tablename__ = "contexts"

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), default="markdown", nullable=False)
    context_type: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[str | None] = mapped_column(String, nullable=True)
    is_pinned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_archived: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="uq_contexts_workspace_slug"),
    )

    # Relationships
    category: Mapped[Category | None] = relationship("Category", back_populates="contexts")
    versions: Mapped[list[ContextVersion]] = relationship(
        "ContextVersion",
        back_populates="context",
        cascade="all, delete-orphan",
    )
    embeddings: Mapped[list[ContextEmbedding]] = relationship(
        "ContextEmbedding",
        back_populates="context",
        cascade="all, delete-orphan",
    )
    usages: Mapped[list[ContextUsage]] = relationship(
        "ContextUsage",
        back_populates="context",
        cascade="all, delete-orphan",
    )
    health_scores: Mapped[list[ContextHealthScore]] = relationship(
        "ContextHealthScore",
        back_populates="context",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list[Tag]] = relationship("Tag", secondary=context_tags, lazy="selectin")


class ContextVersion(BaseModel):
    """Immutable version history for a Context."""

    __tablename__ = "context_versions"

    context_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("contexts.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    context_type: Mapped[str] = mapped_column(String(50), nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[str] = mapped_column(String(50), default="user", nullable=False)

    __table_args__ = (
        UniqueConstraint("context_id", "version_number", name="uq_context_versions_id_number"),
    )

    # Relationships
    context: Mapped[Context] = relationship("Context", back_populates="versions")


class ContextDependency(BaseModel):
    """Directed edge in the Context DAG."""

    __tablename__ = "context_dependencies"

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("contexts.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("contexts.id", ondelete="CASCADE"),
        nullable=False,
    )
    dependency_type: Mapped[str] = mapped_column(String(50), default="requires", nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("source_id", "target_id", name="uq_context_dependencies_source_target"),
    )


class ContextEmbedding(BaseModel):
    """Vector embedding for semantic search (stored as JSON array)."""

    __tablename__ = "context_embeddings"

    context_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("contexts.id", ondelete="CASCADE"),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string representing float array
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        UniqueConstraint("context_id", "model_name", name="uq_context_embeddings_id_model"),
    )

    # Relationships
    context: Mapped[Context] = relationship("Context", back_populates="embeddings")


class ContextUsage(BaseModel):
    """Usage log tracking when a context was included in a prompt run."""

    __tablename__ = "context_usages"

    context_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("contexts.id", ondelete="CASCADE"),
        nullable=False,
    )
    prompt_run_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("prompt_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    used_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
    was_helpful: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0 or 1
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    context: Mapped[Context] = relationship("Context", back_populates="usages")


class ContextHealthScore(BaseModel):
    """Periodic health assessment details of contexts."""

    __tablename__ = "context_health_scores"

    context_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("contexts.id", ondelete="CASCADE"),
        nullable=False,
    )
    overall_health: Mapped[float] = mapped_column(Float, nullable=False)
    freshness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    usage_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    issues: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string representing problems
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string representing advice
    evaluated_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)

    # Relationships
    context: Mapped[Context] = relationship("Context", back_populates="health_scores")
