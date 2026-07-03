"""Analytics and Audit log models."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AnalyticsEvent(BaseModel):
    """Event stream for analytics dashboard."""

    __tablename__ = "analytics_events"

    workspace_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    event_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON payload string


class AuditLog(BaseModel):
    """Security and change audit trail."""

    __tablename__ = "audit_log"

    action: Mapped[str] = mapped_column(String(50), nullable=False)  # create | update | delete | login | export | import
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON snapshot before change
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON snapshot after change
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(1024), nullable=True)
