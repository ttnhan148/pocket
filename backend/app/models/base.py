"""Base database model with common fields and DeclarativeBase."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def generate_uuid() -> str:
    """Generate a standard UUIDv4 string."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Return the current datetime in UTC timezone."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Declarative Base class for SQLAlchemy metadata registry."""



class BaseModel(Base):
    """Base class for standard SQLAlchemy database models with UUID primary keys."""

    __abstract__ = True

    # Primary key UUID
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        index=True,
    )

    # Common timestamp fields stored as datetime in UTC timezone
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Soft delete support
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert the model instance into a dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
