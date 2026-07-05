"""Unit tests for logical modules: Health Score calculation and Markdown parsing (M47)."""

from __future__ import annotations

import pytest
from app.features.workspace.import_export_service import ImportExportService
from app.models import Workspace, Context


@pytest.mark.asyncio
async def test_import_context_markdown_variations(db_session) -> None:
    """Verify ImportExportService parses markdown variations correctly with a valid workspace."""
    # Create a workspace with slug to satisfy NOT NULL constraint
    ws = Workspace(name="MD Test Workspace", slug="md-test-workspace")
    db_session.add(ws)
    await db_session.commit()

    service = ImportExportService(db_session)

    # 1. Test markdown WITH frontmatter
    md_content = (
        "---\n"
        "title: Advanced Physics\n"
        "context_type: persona\n"
        "tags: [science, academic]\n"
        "priority: 90\n"
        "---\n"
        "Body content of physics context."
    )
    ctx1 = await service.import_context_markdown(ws.id, "physics.md", md_content)
    assert ctx1.title == "Advanced Physics"
    assert ctx1.context_type == "persona"
    assert ctx1.content == "Body content of physics context."

    # 2. Test markdown WITHOUT frontmatter
    md_no_fm = "Plain body text without yaml block."
    ctx2 = await service.import_context_markdown(ws.id, "plain_doc.md", md_no_fm)
    # Falls back to converting filename to title
    assert ctx2.title == "Plain Doc"
    assert ctx2.content == "Plain body text without yaml block."
    assert ctx2.context_type == "knowledge"
