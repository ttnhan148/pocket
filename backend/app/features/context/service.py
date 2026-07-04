"""Context Service layer."""

from __future__ import annotations

from typing import Any

import tiktoken
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.core.service import BaseService
from app.features.context.repository import ContextRepository
from app.features.context.schemas import ContextCreate, ContextUpdate
from app.models import Category, Context, ContextVersion, Tag, Workspace


class ContextService(BaseService):
    """Business logic service for managing Contexts and ContextVersions."""

    def __init__(self, db: Any) -> None:
        super().__init__(db)
        self.repo = ContextRepository(db)

    def _estimate_token_count(self, text: str) -> int:
        """Estimate the token count of a string using tiktoken (cl100k_base)."""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            return len(text) // 4

    async def create_context(self, workspace_id: str, data: ContextCreate) -> Context:
        """Create a new context, generate its unique slug, calculate token count, and insert version 1."""
        # Verify workspace existence
        stmt = select(Workspace).where(Workspace.id == workspace_id, Workspace.deleted_at.is_(None))
        workspace_exists = (await self.db.execute(stmt)).scalar() is not None
        if not workspace_exists:
            raise NotFoundError("Workspace", workspace_id)

        # Slug conflict resolution inside the workspace
        slug = slugify(data.title)
        existing = await self.repo.get_by_slug(workspace_id, slug)
        if existing:
            original_slug = slug
            counter = 2
            while existing:
                slug = f"{original_slug}-{counter}"
                existing = await self.repo.get_by_slug(workspace_id, slug)
                counter += 1

        category_id = None
        if data.category_id:
            cat_stmt = select(Category).where(Category.id == data.category_id)
            cat_res = await self.db.execute(cat_stmt)
            if not cat_res.scalar_one_or_none():
                raise NotFoundError(data.category_id, "Category")
            category_id = data.category_id

        token_count = self._estimate_token_count(data.content)

        context = Context(
            workspace_id=workspace_id,
            slug=slug,
            title=data.title,
            content=data.content,
            context_type=data.context_type,
            priority=data.priority,
            confidence=data.confidence,
            token_count=token_count,
            current_version=1,
            metadata_json=data.metadata_json,
            category_id=category_id,
        )

        if data.tag_ids:
            tags_stmt = select(Tag).where(Tag.id.in_(data.tag_ids))
            tags_res = await self.db.execute(tags_stmt)
            context.tags = list(tags_res.scalars().all())

        created_context = await self.repo.create(context)

        version = ContextVersion(
            context_id=created_context.id,
            version_number=1,
            title=data.title,
            content=data.content,
            content_type="markdown",
            context_type=data.context_type,
        )
        self.db.add(version)
        await self.db.flush()

        # Refresh to eager load tags
        refreshed_stmt = select(Context).options(selectinload(Context.tags)).where(Context.id == created_context.id)
        refreshed_res = await self.db.execute(refreshed_stmt)
        return refreshed_res.scalar_one()


    async def get_context(self, workspace_id: str, context_id: str) -> Context:
        """Retrieve a context, raising NotFoundError if it does not exist or belongs to another workspace."""
        context = await self.repo.get_or_raise(context_id)
        if context.workspace_id != workspace_id:
            raise NotFoundError("Context", context_id)
        return context

    async def list_contexts(
        self,
        workspace_id: str,
        context_type: str | None = None,
        is_pinned: int | None = None,
        is_archived: int = 0,
        tag_name: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Context]:
        """List contexts inside a workspace with optional filters."""
        return await self.repo.list_by_workspace(
            workspace_id=workspace_id,
            context_type=context_type,
            is_pinned=is_pinned,
            is_archived=is_archived,
            tag_name=tag_name,
            skip=skip,
            limit=limit,
        )

    async def update_context(self, workspace_id: str, context_id: str, data: ContextUpdate) -> Context:
        """Update context. If title or content changes, increment version and create ContextVersion record."""
        context = await self.get_context(workspace_id, context_id)

        update_dict: dict[str, Any] = {}
        create_new_version = False
        new_title = context.title
        new_content = context.content

        if data.title is not None and data.title != context.title:
            # Check unique slug constraint in this workspace
            new_slug = slugify(data.title)
            existing = await self.repo.get_by_slug(workspace_id, new_slug)
            if existing and existing.id != context_id:
                raise ConflictError(f"Context with title '{data.title}' (slug '{new_slug}') already exists")
            update_dict["title"] = data.title
            update_dict["slug"] = new_slug
            new_title = data.title
            create_new_version = True

        if data.content is not None and data.content != context.content:
            update_dict["content"] = data.content
            update_dict["token_count"] = self._estimate_token_count(data.content)
            new_content = data.content
            create_new_version = True

        if data.priority is not None:
            update_dict["priority"] = data.priority
        if data.confidence is not None:
            update_dict["confidence"] = data.confidence
        if data.is_pinned is not None:
            update_dict["is_pinned"] = data.is_pinned
        if data.is_archived is not None:
            update_dict["is_archived"] = data.is_archived
        if data.metadata_json is not None:
            update_dict["metadata_json"] = data.metadata_json

        if data.category_id is not None:
            if data.category_id:
                cat_stmt = select(Category).where(Category.id == data.category_id)
                cat_res = await self.db.execute(cat_stmt)
                if not cat_res.scalar_one_or_none():
                    raise NotFoundError(data.category_id, "Category")
                update_dict["category_id"] = data.category_id
            else:
                update_dict["category_id"] = None

        if data.tag_ids is not None:
            if data.tag_ids:
                tag_stmt = select(Tag).where(Tag.id.in_(data.tag_ids))
                tag_res = await self.db.execute(tag_stmt)
                context.tags = list(tag_res.scalars().all())
            else:
                context.tags = []
            await self.db.flush()

        # Apply updates
        updated_context = await self.repo.update(context_id, update_dict)

        # Create new version if needed
        if create_new_version:
            next_version = updated_context.current_version + 1
            updated_context.current_version = next_version

            version_record = ContextVersion(
                context_id=context_id,
                version_number=next_version,
                title=new_title,
                content=new_content,
                content_type="markdown",
                context_type=context.context_type,
            )
            self.db.add(version_record)
            await self.db.flush()

        # Refresh to eager load tags
        refreshed_stmt = select(Context).options(selectinload(Context.tags)).where(Context.id == updated_context.id)
        refreshed_res = await self.db.execute(refreshed_stmt)
        return refreshed_res.scalar_one()


    async def list_versions(self, workspace_id: str, context_id: str) -> list[ContextVersion]:
        """List all version history records for a context."""
        await self.get_context(workspace_id, context_id)  # Validate context exists and belongs to workspace
        stmt = select(ContextVersion).where(ContextVersion.context_id == context_id).order_by(ContextVersion.version_number.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def delete_context(self, workspace_id: str, context_id: str) -> bool:
        """Soft delete context by ID."""
        await self.get_context(workspace_id, context_id)  # Validate exists in workspace
        return await self.repo.delete(context_id, soft=True)

    async def search_contexts(self, workspace_id: str, query: str) -> list[Context]:
        """Full text search contexts within a workspace."""
        return await self.repo.search(workspace_id, query)

    async def update_scores(
        self, context_id: str, delta_confidence: float, delta_usage: int
    ) -> Context:
        """Update context confidence and usage scores based on learning feedback."""
        stmt = select(Context).where(Context.id == context_id, Context.deleted_at.is_(None))
        res = await self.db.execute(stmt)
        context = res.scalar_one_or_none()
        if not context:
            raise NotFoundError("Context", context_id)
        
        context.confidence = max(0.0, min(1.0, context.confidence + delta_confidence))
        context.usage_count += delta_usage
        await self.db.flush()
        return context
