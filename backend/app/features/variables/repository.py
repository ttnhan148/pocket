"""Variable Repository subclassing BaseRepository."""

from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.models import Variable, WorkspaceVariable


class VariableRepository(BaseRepository[Variable]):
    """Repository class for database access on Variable models."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Variable, db)

    async def get_by_name(self, name: str, scope: str = "global") -> Variable | None:
        """Fetch a variable by its name and scope, ignoring soft-deleted items."""
        stmt = (
            select(Variable)
            .where(
                Variable.name == name,
                Variable.scope == scope,
                Variable.deleted_at.is_(None),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_variables(self, scope: str | None = None) -> list[Variable]:
        """List variables with optional scope filter."""
        stmt = select(Variable).where(Variable.deleted_at.is_(None))
        if scope:
            stmt = stmt.where(Variable.scope == scope)
        stmt = stmt.order_by(Variable.sort_order.asc(), Variable.name.asc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_workspace_override(self, workspace_id: str, variable_id: str) -> WorkspaceVariable | None:
        """Get workspace variable override for a specific variable."""
        stmt = (
            select(WorkspaceVariable)
            .where(
                WorkspaceVariable.workspace_id == workspace_id,
                WorkspaceVariable.variable_id == variable_id,
                WorkspaceVariable.deleted_at.is_(None),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_workspace_overrides(self, workspace_id: str) -> list[WorkspaceVariable]:
        """List all overrides for a workspace."""
        stmt = (
            select(WorkspaceVariable)
            .where(
                WorkspaceVariable.workspace_id == workspace_id,
                WorkspaceVariable.deleted_at.is_(None),
            )
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def save_workspace_override(self, workspace_id: str, variable_id: str, value: str | None) -> WorkspaceVariable:
        """Save (Insert/Update) a workspace override value."""
        override = await self.get_workspace_override(workspace_id, variable_id)
        if override:
            override.value = value
            # Since WorkspaceVariable inherits from BaseModel, let's update it.
            # We don't have to trigger anything special, just changing attribute will flush.
        else:
            override = WorkspaceVariable(
                workspace_id=workspace_id,
                variable_id=variable_id,
                value=value,
            )
            self.db.add(override)
        await self.db.flush()
        return override
