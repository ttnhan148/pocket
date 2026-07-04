"""Journal Service layer (M44)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.service import BaseService
from app.models.journal import Journal
from app.models.workspace import Workspace
from app.features.journals.schemas import JournalCreate, JournalUpdate


class JournalService(BaseService):
    """Business logic for Managing Conversation Journals."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def create_journal(self, data: JournalCreate) -> Journal:
        """Create a new journal entry."""
        if data.workspace_id:
            stmt = select(Workspace).where(Workspace.id == data.workspace_id, Workspace.deleted_at.is_(None))
            workspace_exists = (await self.db.execute(stmt)).scalar() is not None
            if not workspace_exists:
                raise NotFoundError("Workspace", data.workspace_id)

        journal = Journal(
            workspace_id=data.workspace_id,
            title=data.title,
            content=data.content,
            mood=data.mood,
            tags_json=json.dumps(data.tags) if data.tags else "[]",
            is_pinned=0,
        )
        self.db.add(journal)
        await self.db.flush()
        return journal

    async def get_journal(self, journal_id: str) -> Journal:
        """Retrieve a journal by its ID."""
        stmt = select(Journal).where(Journal.id == journal_id, Journal.deleted_at.is_(None))
        journal = (await self.db.execute(stmt)).scalar_one_or_none()
        if not journal:
            raise NotFoundError("Journal", journal_id)
        return journal

    async def list_journals(
        self,
        workspace_id: str | None = None,
        query: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Journal]:
        """List active journals with options to search and filter by workspace."""
        stmt = select(Journal).where(Journal.deleted_at.is_(None))

        if workspace_id:
            stmt = stmt.where(Journal.workspace_id == workspace_id)

        if query and query.strip():
            q_pattern = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    Journal.title.ilike(q_pattern),
                    Journal.content.ilike(q_pattern),
                )
            )

        stmt = stmt.order_by(Journal.is_pinned.desc(), Journal.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def update_journal(self, journal_id: str, data: JournalUpdate) -> Journal:
        """Update fields of an existing journal entry."""
        journal = await self.get_journal(journal_id)

        if data.title is not None:
            journal.title = data.title
        if data.content is not None:
            journal.content = data.content
        if data.mood is not None:
            journal.mood = data.mood
        if data.tags is not None:
            journal.tags_json = json.dumps(data.tags)
        if data.is_pinned is not None:
            journal.is_pinned = data.is_pinned

        await self.db.flush()
        return journal

    async def delete_journal(self, journal_id: str) -> None:
        """Soft delete a journal entry."""
        journal = await self.get_journal(journal_id)
        journal.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
