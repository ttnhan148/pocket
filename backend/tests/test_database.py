"""Model CRUD and database integration tests."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Context, Tag, Workspace


@pytest.mark.asyncio
async def test_workspace_crud(db_session: AsyncSession) -> None:
    """Verify Workspace creation, reading, updating, and deleting."""
    # Create
    workspace = Workspace(
        name="Test Workspace",
        slug="test-workspace",
        description="A workspace for unit testing",
        is_default=1,
    )
    db_session.add(workspace)
    await db_session.flush()

    workspace_id = workspace.id
    assert workspace_id is not None

    # Read
    stmt = select(Workspace).where(Workspace.id == workspace_id)
    res = await db_session.execute(stmt)
    db_workspace = res.scalar_one()
    assert db_workspace.name == "Test Workspace"
    assert db_workspace.is_default == 1

    # Update
    db_workspace.name = "Updated Workspace"
    await db_session.flush()

    res = await db_session.execute(select(Workspace).where(Workspace.id == workspace_id))
    assert res.scalar_one().name == "Updated Workspace"

    # Delete
    await db_session.delete(db_workspace)
    await db_session.flush()

    res = await db_session.execute(select(Workspace).where(Workspace.id == workspace_id))
    assert res.scalar() is None


@pytest.mark.asyncio
async def test_foreign_key_constraints(db_session: AsyncSession) -> None:
    """Verify context cannot be created with a non-existent workspace_id."""
    context = Context(
        workspace_id="non-existent-uuid",
        title="Invalid Context",
        slug="invalid-context",
        content="Invalid workspace reference.",
        context_type="knowledge",
    )
    db_session.add(context)

    # SQLite foreign keys are checked on commit/flush
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_cascade_delete(db_session: AsyncSession) -> None:
    """Verify deleting a workspace cascades and deletes its contexts."""
    # Create Workspace
    workspace = Workspace(name="Cascade Workspace", slug="cascade-workspace")
    db_session.add(workspace)
    await db_session.flush()

    # Create Context under Workspace
    context = Context(
        workspace_id=workspace.id,
        title="Cascaded Context",
        slug="cascaded-context",
        content="This context should be deleted if the workspace is deleted.",
        context_type="instruction",
    )
    db_session.add(context)
    await db_session.flush()

    context_id = context.id

    # Verify context exists
    res = await db_session.execute(select(Context).where(Context.id == context_id))
    assert res.scalar() is not None

    # Delete Workspace
    await db_session.delete(workspace)
    await db_session.flush()

    # Verify context is deleted
    res = await db_session.execute(select(Context).where(Context.id == context_id))
    assert res.scalar() is None


@pytest.mark.asyncio
async def test_context_tagging(db_session: AsyncSession) -> None:
    """Verify contexts can be tagged using junction table."""
    # Create Workspace
    workspace = Workspace(name="Tag Workspace", slug="tag-workspace")
    db_session.add(workspace)
    await db_session.flush()

    # Create Tag
    tag = Tag(name="Python", slug="python")
    db_session.add(tag)
    await db_session.flush()

    # Create Context with associated tag in constructor
    context = Context(
        workspace_id=workspace.id,
        title="Tagged Context",
        slug="tagged-context",
        content="Tagged content.",
        context_type="persona",
        tags=[tag],
    )
    db_session.add(context)
    await db_session.flush()

    # Query context with tags loaded
    stmt = select(Context).where(Context.id == context.id)
    res = await db_session.execute(stmt)
    db_context = res.scalar_one()

    assert len(db_context.tags) == 1
    assert db_context.tags[0].name == "Python"
