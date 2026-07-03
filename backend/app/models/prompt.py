"""PromptRun and compilation history models."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PromptRun(BaseModel):
    """Records of every prompt compilation and execution."""

    __tablename__ = "prompt_runs"

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    conversation_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    template_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_input: Mapped[str] = mapped_column(Text, nullable=False)
    compiled_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    validation_passed: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    validation_errors: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    optimization_applied: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    variables_used: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON object
    metadata_json: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)

    # Relationships
    contexts: Mapped[list[PromptContext]] = relationship(
        "PromptContext",
        back_populates="prompt_run",
        cascade="all, delete-orphan",
    )
    versions: Mapped[list[PromptVersion]] = relationship(
        "PromptVersion",
        back_populates="prompt_run",
        cascade="all, delete-orphan",
    )
    score: Mapped[PromptScore | None] = relationship(
        "PromptScore",
        back_populates="prompt_run",
        cascade="all, delete-orphan",
        uselist=False,
    )


class PromptContext(BaseModel):
    """Junction table recording which contexts were included in a prompt run."""

    __tablename__ = "prompt_contexts"

    prompt_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("prompt_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    context_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("contexts.id", ondelete="CASCADE"),
        nullable=False,
    )
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    was_auto_included: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("prompt_run_id", "context_id", name="uq_prompt_contexts_run_context"),
    )

    # Relationships
    prompt_run: Mapped[PromptRun] = relationship("PromptRun", back_populates="contexts")


class PromptVersion(BaseModel):
    """Snapshots of compiled prompts at different stages."""

    __tablename__ = "prompt_versions"

    prompt_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("prompt_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)  # raw | compiled | optimized | enhanced | final

    # Relationships
    prompt_run: Mapped[PromptRun] = relationship("PromptRun", back_populates="versions")


class PromptScore(BaseModel):
    """Quality scores evaluated for compiled prompts."""

    __tablename__ = "prompt_scores"

    prompt_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("prompt_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    clarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    specificity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    completeness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    consistency_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    efficiency_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggestions: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    model: Mapped[str] = mapped_column(String(100), nullable=False)

    __table_args__ = (
        UniqueConstraint("prompt_run_id", name="uq_prompt_scores_run"),
    )

    # Relationships
    prompt_run: Mapped[PromptRun] = relationship("PromptRun", back_populates="score")
