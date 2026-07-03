"""AI background processing jobs and results models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class AIJob(BaseModel):
    """Background AI processing tasks."""

    __tablename__ = "ai_jobs"

    job_type: Mapped[str] = mapped_column(String(100), nullable=False)  # embedding | tagging | scoring | review | learning | health_check
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending | running | completed | failed | cancelled
    input_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON input string
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0.0 to 1.0
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    results: Mapped[list[AIJobResult]] = relationship(
        "AIJobResult",
        back_populates="job",
        cascade="all, delete-orphan",
    )


class AIJobResult(BaseModel):
    """Results produced by AI background jobs."""

    __tablename__ = "ai_job_results"

    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ai_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    result_type: Mapped[str] = mapped_column(String(100), nullable=False)  # embedding | tag_suggestion | score | context_candidate | review
    result_data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON result string
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # context | template | conversation
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    applied: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0 or 1

    # Relationships
    job: Mapped[AIJob] = relationship("AIJob", back_populates="results")
