"""Workspace Service layer."""

from __future__ import annotations

from typing import Any

from slugify import slugify
from sqlalchemy import select

from app.core.exceptions import ConflictError, ValidationError
from app.core.service import BaseService
from app.features.workspace.repository import WorkspaceRepository
from app.features.workspace.schemas import WorkspaceCreate, WorkspaceUpdate
from app.models import Workspace


class WorkspaceService(BaseService):
    """Business logic service for managing Workspaces."""

    def __init__(self, db: Any) -> None:
        super().__init__(db)
        self.repo = WorkspaceRepository(db)

    async def create_workspace(self, data: WorkspaceCreate) -> Workspace:
        """Create a new workspace, slugify name, and resolve default workspace flag."""
        slug = slugify(data.name)
        existing = await self.repo.get_by_slug(slug)
        if existing:
            # Suffix increment resolver for duplicates
            original_slug = slug
            counter = 2
            while existing:
                slug = f"{original_slug}-{counter}"
                existing = await self.repo.get_by_slug(slug)
                counter += 1

        # Check if this is the first active workspace
        stmt = select(Workspace).where(Workspace.deleted_at.is_(None))
        res = await self.db.execute(stmt)
        workspaces_count = len(res.scalars().all())
        is_default = 1 if workspaces_count == 0 else 0

        workspace = Workspace(
            name=data.name,
            slug=slug,
            description=data.description,
            icon=data.icon,
            color=data.color,
            is_default=is_default,
            metadata_json=data.metadata_json,
        )

        return await self.repo.create(workspace)

    async def get_workspace(self, workspace_id: str) -> Workspace:
        """Retrieve workspace by ID or raise NotFoundError."""
        return await self.repo.get_or_raise(workspace_id)

    async def get_workspace_by_slug(self, slug: str) -> Workspace:
        """Retrieve active workspace by slug or raise Conflict/ValidationError."""
        workspace = await self.repo.get_by_slug(slug)
        if workspace is None:
            raise ValidationError(f"Workspace with slug '{slug}' not found")
        return workspace

    async def list_workspaces(self, skip: int = 0, limit: int = 100) -> list[Workspace]:
        """List active workspaces ordered by sort_order ASC."""
        return await self.repo.list_ordered(skip, limit)

    async def update_workspace(self, workspace_id: str, data: WorkspaceUpdate) -> Workspace:
        """Update workspace fields. Does not allow slug updates once created."""
        workspace = await self.get_workspace(workspace_id)

        update_dict: dict[str, Any] = {}
        if data.name is not None and data.name != workspace.name:
            # Verify new name doesn't conflict with active workspaces
            stmt = select(Workspace).where(
                Workspace.name == data.name,
                Workspace.id != workspace_id,
                Workspace.deleted_at.is_(None),
            )
            res = await self.db.execute(stmt)
            if res.scalar():
                raise ConflictError(f"Workspace with name '{data.name}' already exists")
            update_dict["name"] = data.name

        if data.description is not None:
            update_dict["description"] = data.description
        if data.icon is not None:
            update_dict["icon"] = data.icon
        if data.color is not None:
            update_dict["color"] = data.color
        if data.sort_order is not None:
            update_dict["sort_order"] = data.sort_order
        if data.metadata_json is not None:
            update_dict["metadata_json"] = data.metadata_json

        return await self.repo.update(workspace_id, update_dict)

    async def set_default_workspace(self, workspace_id: str) -> Workspace:
        """Set a target workspace as default and reset the previous default workspace."""
        target = await self.get_workspace(workspace_id)
        if target.is_default == 1:
            return target

        # Find current default
        current_default = await self.repo.get_default()
        if current_default:
            current_default.is_default = 0

        target.is_default = 1
        await self.db.flush()
        return target

    async def delete_workspace(self, workspace_id: str, soft: bool = True) -> bool:
        """Delete workspace. Prevents deletion of default workspace."""
        workspace = await self.get_workspace(workspace_id)
        if workspace.is_default == 1:
            raise ValidationError("Cannot delete the default workspace. Set another workspace as default first.")

        return await self.repo.delete(workspace_id, soft=soft)
