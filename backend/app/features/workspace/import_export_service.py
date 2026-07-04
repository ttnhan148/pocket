"""Import/Export Service layer (M45)."""

from __future__ import annotations

import yaml
import re
import json
import logging
from typing import Any, Dict
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.service import BaseService
from app.models import Workspace, Context, Template, Variable, Tag
from app.features.context.service import ContextService
from app.features.context.schemas import ContextCreate
from app.features.tags_categories.service import TagService
from app.features.tags_categories.schemas import TagCreate

logger = logging.getLogger("pocket.features.workspace.import_export_service")


class ImportExportService(BaseService):
    """Business logic for Workspace data import and export."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self._context_service = ContextService(db)
        self._tag_service = TagService(db)

    async def export_workspace(self, workspace_id: str) -> Dict[str, Any]:
        """Export all contexts, templates, and variables of a workspace as JSON."""
        # 1. Verify workspace
        stmt = select(Workspace).where(Workspace.id == workspace_id, Workspace.deleted_at.is_(None))
        workspace = (await self.db.execute(stmt)).scalar_one_or_none()
        if not workspace:
            raise NotFoundError("Workspace", workspace_id)

        # 2. Fetch contexts with tags
        ctx_stmt = (
            select(Context)
            .options(selectinload(Context.tags))
            .where(Context.workspace_id == workspace_id, Context.deleted_at.is_(None))
        )
        contexts = (await self.db.execute(ctx_stmt)).scalars().all()

        contexts_data = []
        for c in contexts:
            contexts_data.append({
                "title": c.title,
                "content": c.content,
                "context_type": c.context_type,
                "priority": c.priority,
                "confidence": c.confidence,
                "tags": [t.name for t in c.tags],
                "metadata_json": c.metadata_json,
            })

        # 3. Fetch templates
        tmpl_stmt = (
            select(Template)
            .where(Template.workspace_id == workspace_id, Template.deleted_at.is_(None))
        )
        templates = (await self.db.execute(tmpl_stmt)).scalars().all()

        templates_data = []
        for t in templates:
            templates_data.append({
                "title": t.title,
                "content": t.content,
                "description": t.description,
                "schema_json": t.schema_json,
            })

        return {
            "version": "1.0.0",
            "workspace_name": workspace.name,
            "contexts": contexts_data,
            "templates": templates_data,
        }

    async def import_workspace_json(self, workspace_id: str, data: Dict[str, Any]) -> Dict[str, int]:
        """Import contexts and templates from exported JSON workspace data."""
        # Verify workspace
        stmt = select(Workspace).where(Workspace.id == workspace_id, Workspace.deleted_at.is_(None))
        workspace_exists = (await self.db.execute(stmt)).scalar_one_or_none() is not None
        if not workspace_exists:
            raise NotFoundError("Workspace", workspace_id)

        contexts_imported = 0
        templates_imported = 0

        # Import Contexts
        contexts = data.get("contexts", [])
        for c in contexts:
            # Resolve tags
            tag_ids = []
            tags = c.get("tags", [])
            for t_name in tags:
                if t_name.strip():
                    try:
                        tag_obj = await self._tag_service.create_tag(
                            TagCreate(name=t_name.strip().lower())
                        )
                        tag_ids.append(tag_obj.id)
                    except Exception as e:
                        logger.warning(f"Failed to resolve tag {t_name}: {e}")

            # Avoid duplication by title
            check_stmt = select(Context).where(
                Context.workspace_id == workspace_id,
                Context.title == c["title"],
                Context.deleted_at.is_(None)
            )
            existing = (await self.db.execute(check_stmt)).scalar_one_or_none()
            if existing:
                # Update content and tags
                existing.content = c["content"]
                existing.context_type = c.get("context_type", "knowledge")
                if tag_ids:
                    tags_objs = (await self.db.execute(select(Tag).where(Tag.id.in_(tag_ids)))).scalars().all()
                    existing.tags = list(tags_objs)
            else:
                create_payload = ContextCreate(
                    title=c["title"],
                    content=c["content"],
                    context_type=c.get("context_type", "knowledge"),
                    priority=c.get("priority", 50),
                    confidence=c.get("confidence", 1.0),
                    tag_ids=tag_ids,
                )
                await self._context_service.create_context(workspace_id, create_payload)
            contexts_imported += 1

        # Import Templates
        templates = data.get("templates", [])
        for t in templates:
            # Avoid duplicate template by title
            check_tmpl = select(Template).where(
                Template.workspace_id == workspace_id,
                Template.title == t["title"],
                Template.deleted_at.is_(None)
            )
            existing_tmpl = (await self.db.execute(check_tmpl)).scalar_one_or_none()
            if existing_tmpl:
                existing_tmpl.content = t["content"]
                existing_tmpl.description = t.get("description")
                existing_tmpl.schema_json = t.get("schema_json")
            else:
                from slugify import slugify
                new_tmpl = Template(
                    workspace_id=workspace_id,
                    title=t["title"],
                    slug=slugify(t["title"]),
                    content=t["content"],
                    description=t.get("description"),
                    schema_json=t.get("schema_json"),
                )
                self.db.add(new_tmpl)
            templates_imported += 1

        return {
            "contexts_imported": contexts_imported,
            "templates_imported": templates_imported,
        }

    async def import_context_markdown(self, workspace_id: str, filename: str, content: str) -> Context:
        """Parse markdown YAML frontmatter and create or update context."""
        # Match yaml frontmatter
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        
        if not match:
            # Fallback when no frontmatter
            title = filename.replace(".md", "").replace("_", " ").title()
            body_content = content
            metadata = {}
        else:
            frontmatter_str, body_content = match.groups()
            try:
                metadata = yaml.safe_load(frontmatter_str) or {}
            except Exception:
                metadata = {}
            title = metadata.get("title", filename.replace(".md", "").replace("_", " ").title())

        # Resolve tags
        tag_ids = []
        tags = metadata.get("tags", [])
        if isinstance(tags, list):
            for t_name in tags:
                if isinstance(t_name, str) and t_name.strip():
                    try:
                        tag_obj = await self._tag_service.create_tag(
                            TagCreate(name=t_name.strip().lower())
                        )
                        tag_ids.append(tag_obj.id)
                    except Exception as e:
                        logger.warning(f"Failed to resolve tag {t_name}: {e}")

        # Check existing context by title
        check_stmt = select(Context).where(
            Context.workspace_id == workspace_id,
            Context.title == title,
            Context.deleted_at.is_(None)
        )
        existing = (await self.db.execute(check_stmt)).scalar_one_or_none()
        if existing:
            existing.content = body_content.strip()
            existing.context_type = metadata.get("context_type", "knowledge")
            if tag_ids:
                tags_objs = (await self.db.execute(select(Tag).where(Tag.id.in_(tag_ids)))).scalars().all()
                existing.tags = list(tags_objs)
            return existing
        else:
            create_payload = ContextCreate(
                title=title,
                content=body_content.strip(),
                context_type=metadata.get("context_type", "knowledge"),
                priority=metadata.get("priority", 50),
                confidence=metadata.get("confidence", 1.0),
                tag_ids=tag_ids,
            )
            return await self._context_service.create_context(workspace_id, create_payload)
