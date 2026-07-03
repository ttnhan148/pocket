"""Database engine, session factory, and SQLite PRAGMA configuration."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings

# Module-level references (initialized in init_db)
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _set_sqlite_pragmas(dbapi_connection: Any, _connection_record: object) -> None:
    """Configure SQLite PRAGMAs on every new connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA busy_timeout = 5000")
    cursor.execute("PRAGMA cache_size = -64000")
    cursor.execute("PRAGMA mmap_size = 268435456")
    cursor.execute("PRAGMA temp_store = MEMORY")
    cursor.execute("PRAGMA auto_vacuum = INCREMENTAL")
    cursor.close()


async def init_db(settings: Settings) -> None:
    """Initialize the database engine and ensure the DB directory exists."""
    global _engine, _session_factory  # noqa: PLW0603

    # Ensure database directory exists
    db_path = os.path.expanduser(settings.db_path)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    kwargs: dict[str, Any] = {
        "echo": settings.env == "development",
        "pool_pre_ping": True,
    }
    # SQLite in-memory database does not support standard QueuePool arguments
    if ":memory:" not in settings.database_url:
        kwargs["pool_size"] = 5
        kwargs["max_overflow"] = 10

    _engine = create_async_engine(settings.database_url, **kwargs)

    # Set PRAGMAs on the sync driver level
    event.listen(_engine.sync_engine, "connect", _set_sqlite_pragmas)

    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


def get_engine() -> AsyncEngine:
    """Get the database engine. Raises if not initialized."""
    if _engine is None:
        msg = "Database not initialized. Call init_db() first."
        raise RuntimeError(msg)
    return _engine


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yields an async database session."""
    if _session_factory is None:
        msg = "Database not initialized. Call init_db() first."
        raise RuntimeError(msg)
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_connection() -> bool:
    """Check if database connection is healthy."""
    if _engine is None:
        return False
    try:
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
