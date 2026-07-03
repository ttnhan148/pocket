"""Post-conversation learning and context candidate models."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class LearningRecord(BaseModel):
    """Post-conversation learning analysis and suggestions."""

    __tablename__ = "learning_records"

    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    analysis: Mapped[str] = mapped_column(Text, nullable=False)  # JSON analysis string
    missing_contexts: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    success_factors: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    failure_factors: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    applied: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0 or 1

    # Relationships
    candidates: Mapped[list[ContextCandidate]] = relationship(
        "ContextCandidate",
        back_populates="learning_record",
        cascade="all, delete-orphan",
    )


class ContextCandidate(BaseModel):
    """AI-generated context suggestions from learning analysis."""

    __tablename__ = "context_candidates"

    learning_record_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("learning_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    suggested_title: Mapped[str] = mapped_column(String(255), nullable=False)
    suggested_content: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_type: Mapped[str] = mapped_column(String(50), nullable=False)  # context_type enum value
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending | accepted | rejected | merged
    reviewed_at: Mapped[str | None] = mapped_column(String, nullable=True)  # ISO string

    # Relationships
    learning_record: Mapped[LearningRecord] = relationship("LearningRecord", back_populates="candidates")
