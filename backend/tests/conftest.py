"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Generator
from typing import Any

import pytest
import pytest_asyncio
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.core.database import get_engine, init_db
from app.main import create_app
from app.models import Base


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Test settings with in-memory database."""
    return Settings(
        env="testing",
        db_path=":memory:",
        log_level="WARNING",
    )



async def _create_fts_tables(conn: Any) -> None:
    """Create virtual FTS5 tables and synchronization triggers for testing."""
    await conn.execute(sa.text("""
        CREATE VIRTUAL TABLE contexts_fts USING fts5(
            title,
            content,
            context_type,
            content='contexts',
            content_rowid='rowid',
            tokenize='porter unicode61 remove_diacritics 2'
        );
    """))
    await conn.execute(sa.text("""
        CREATE TRIGGER contexts_ai AFTER INSERT ON contexts BEGIN
            INSERT INTO contexts_fts(rowid, title, content, context_type)
            VALUES (new.rowid, new.title, new.content, new.context_type);
        END;
    """))
    await conn.execute(sa.text("""
        CREATE TRIGGER contexts_au AFTER UPDATE ON contexts BEGIN
            INSERT INTO contexts_fts(contexts_fts, rowid, title, content, context_type)
            VALUES ('delete', old.rowid, old.title, old.content, old.context_type);
            INSERT INTO contexts_fts(rowid, title, content, context_type)
            VALUES (new.rowid, new.title, new.content, new.context_type);
        END;
    """))
    await conn.execute(sa.text("""
        CREATE TRIGGER contexts_ad AFTER DELETE ON contexts BEGIN
            INSERT INTO contexts_fts(contexts_fts, rowid, title, content, context_type)
            VALUES ('delete', old.rowid, old.title, old.content, old.context_type);
        END;
    """))


async def _seed_settings(conn: Any) -> None:
    """Seed default settings into the in-memory database."""
    from datetime import datetime, UTC
    now = datetime.now(UTC)
    await conn.execute(sa.text("""
        INSERT INTO settings (key, value, value_type, category, description, updated_at) VALUES
        ('auto_embed', 'true', 'boolean', 'ai', 'Automatically generate embeddings for contexts', :now),
        ('auto_tag', 'true', 'boolean', 'ai', 'Automatically suggest tags for new contexts', :now),
        ('learning_enabled', 'true', 'boolean', 'ai', 'Enable post-conversation learning loop', :now),
        ('theme', 'dark', 'text', 'ui', 'Application theme (light or dark)', :now),
        ('default_model', 'gpt-4.1', 'text', 'ai', 'Default model for chat completions', :now),
        ('token_limit', '128000', 'number', 'ai', 'Default token budget limit', :now),
        ('search_top_k', '10', 'number', 'search', 'Number of contexts to retrieve by default', :now)
    """), {"now": now})


@pytest_asyncio.fixture
async def client(test_settings: Settings) -> AsyncIterator[AsyncClient]:
    """Async HTTP client for testing API endpoints."""
    await init_db(test_settings)
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _create_fts_tables(conn)
        await _seed_settings(conn)

    app = create_app(settings=test_settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(test_settings: Settings) -> AsyncIterator[AsyncSession]:
    """Provide an isolated database session with tables created."""
    await init_db(test_settings)
    engine = get_engine()

    # Create all tables in memory
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _create_fts_tables(conn)
        await _seed_settings(conn)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
