"""Infrastructure unit and integration tests (BaseRepository, logging, exceptions)."""

from __future__ import annotations

import logging

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import setup_logging
from app.core.repository import BaseRepository
from app.models import Workspace


# Create a concrete repository for testing
class WorkspaceRepository(BaseRepository[Workspace]):
    """Concrete repository for Workspace models."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Workspace, db)


@pytest.mark.asyncio
async def test_base_repository_operations(db_session: AsyncSession) -> None:
    """Verify standard CRUD operations via BaseRepository wrapper."""
    repo = WorkspaceRepository(db_session)

    # 1. Create
    workspace = Workspace(name="Repo Workspace", slug="repo-workspace")
    created = await repo.create(workspace)
    assert created.id is not None
    assert created.name == "Repo Workspace"

    # 2. Get (or raise)
    fetched = await repo.get_or_raise(created.id)
    assert fetched.slug == "repo-workspace"

    # 3. List
    all_workspaces = await repo.list()
    assert len(all_workspaces) == 1
    assert all_workspaces[0].name == "Repo Workspace"

    # 4. Update
    updated = await repo.update(created.id, {"name": "New Name"})
    assert updated.name == "New Name"

    # Verify update in DB
    refetched = await repo.get_or_raise(created.id)
    assert refetched.name == "New Name"

    # 5. Soft Delete
    deleted = await repo.delete(created.id, soft=True)
    assert deleted is True

    # Retrieve should now fail / return None due to active_filter
    deleted_check = await repo.get(created.id)
    assert deleted_check is None

    # Retrieve directly via SQLAlchemy query to check soft deleted status
    stmt = select(Workspace).where(Workspace.id == created.id)
    res = await db_session.execute(stmt)
    db_record = res.scalar_one()
    assert db_record.deleted_at is not None

    # Get non-existent raises NotFoundError
    with pytest.raises(NotFoundError):
        await repo.get_or_raise("non-existent-uuid")


def test_structured_logging_setup(caplog: pytest.LogCaptureFixture) -> None:
    """Verify structured logging attaches correct handler and level."""
    from app.config import Settings  # noqa: PLC0415

    settings = Settings(env="production", log_level="DEBUG")
    setup_logging(settings)

    logger = logging.getLogger("pocket_test")
    assert logging.getLogger().level == logging.DEBUG

    caplog.set_level(logging.INFO)
    logger.info("Test structured logging output")

    # The logging handler should be set up
    root_handlers = logging.getLogger().handlers
    assert len(root_handlers) > 0
