"""Template Service layer."""

from __future__ import annotations

from typing import Any
import jinja2
from jinja2 import Environment, meta
import tiktoken
from slugify import slugify
from sqlalchemy import select, delete

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.service import BaseService
from app.features.templates.repository import TemplateRepository
from app.features.templates.schemas import TemplateCreate, TemplateUpdate
from app.models import Template, TemplateVersion, TemplateVariable, Variable, Workspace


class TemplateService(BaseService):
    """Business logic service for managing Prompt Templates and Rendering."""

    def __init__(self, db: Any) -> None:
        super().__init__(db)
        self.repo = TemplateRepository(db)
        self.jinja_env = Environment()

    def _estimate_token_count(self, text: str) -> int:
        """Estimate the token count of a string using tiktoken (cl100k_base)."""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            return len(text) // 4

    def detect_variables(self, content: str) -> list[str]:
        """Parse template content to extract Jinja2 variables."""
        try:
            ast = self.jinja_env.parse(content)
            return sorted(list(meta.find_undeclared_variables(ast)))
        except Exception as e:
            raise ValidationError(f"Invalid Jinja2 syntax: {str(e)}")

    async def _sync_template_variables(self, template_id: str, content: str) -> None:
        """Parse variables from template and update template_variables relationships."""
        detected_names = self.detect_variables(content)
        system_reserved = {"date", "time", "datetime", "workspace_id", "workspace_name", "workspace_slug", "active_provider"}
        sync_names = [n for n in detected_names if n.lower() not in system_reserved]

        # 1. Fetch existing relations
        stmt_existing = select(TemplateVariable).where(TemplateVariable.template_id == template_id)
        existing_relations = list((await self.db.execute(stmt_existing)).scalars().all())
        existing_var_ids = {rel.variable_id: rel for rel in existing_relations}

        # 2. Get or create Variable entries for all detected names
        resolved_var_ids = []
        for name in sync_names:
            stmt_var = select(Variable).where(Variable.name == name, Variable.deleted_at.is_(None))
            variable = (await self.db.execute(stmt_var)).scalar()
            
            if not variable:
                # Auto-create global variable registry if not found
                variable = Variable(
                    name=name,
                    display_name=name.replace("_", " ").title(),
                    description=f"Auto-generated variable from template integration",
                    value_type="text",
                    scope="global",
                )
                self.db.add(variable)
                await self.db.flush()

            resolved_var_ids.append(variable.id)

            # Link if not already linked
            if variable.id not in existing_var_ids:
                link = TemplateVariable(
                    template_id=template_id,
                    variable_id=variable.id,
                    is_required=1,
                )
                self.db.add(link)

        # 3. Remove obsolete links
        for var_id, rel in existing_var_ids.items():
            if var_id not in resolved_var_ids:
                await self.db.delete(rel)

        await self.db.flush()

    async def create_template(self, workspace_id: str, data: TemplateCreate) -> Template:
        """Create a new template, generate version 1, and sync variables."""
        # Verify workspace
        stmt = select(Workspace).where(Workspace.id == workspace_id, Workspace.deleted_at.is_(None))
        workspace = (await self.db.execute(stmt)).scalar()
        if not workspace:
            raise NotFoundError("Workspace", workspace_id)

        # Unique slug resolution
        slug = slugify(data.title)
        existing = await self.repo.get_by_slug(workspace_id, slug)
        if existing:
            original_slug = slug
            counter = 2
            while existing:
                slug = f"{original_slug}-{counter}"
                existing = await self.repo.get_by_slug(workspace_id, slug)
                counter += 1

        # Calculate token count
        token_count = self._estimate_token_count(data.content)

        template = Template(
            workspace_id=workspace_id,
            slug=slug,
            title=data.title,
            description=data.description,
            content=data.content,
            template_type=data.template_type,
            schema_json=data.schema_json,
            default_variables=data.default_variables,
            token_count=token_count,
            current_version=1,
            metadata_json=data.metadata_json,
        )
        created_template = await self.repo.create(template)

        # Version 1 history
        version = TemplateVersion(
            template_id=created_template.id,
            version_number=1,
            content=data.content,
            schema_json=data.schema_json,
            change_summary="Initial creation",
        )
        self.db.add(version)
        await self.db.flush()

        # Sync variables
        await self._sync_template_variables(created_template.id, data.content)

        return created_template

    async def get_template(self, workspace_id: str, template_id: str) -> Template:
        """Retrieve template by ID, validating workspace scoping."""
        template = await self.repo.get_or_raise(template_id)
        if template.workspace_id != workspace_id:
            raise NotFoundError("Template", template_id)
        return template

    async def list_templates(self, workspace_id: str, skip: int = 0, limit: int = 100) -> list[Template]:
        """List templates under a workspace."""
        return await self.repo.list_by_workspace(workspace_id, skip, limit)

    async def update_template(self, workspace_id: str, template_id: str, data: TemplateUpdate) -> Template:
        """Update template, increment version if content/schema changes, and sync variables."""
        template = await self.get_template(workspace_id, template_id)

        update_dict: dict[str, Any] = {}
        create_new_version = False
        new_content = template.content
        new_schema = template.schema_json

        if data.title is not None and data.title != template.title:
            new_slug = slugify(data.title)
            existing = await self.repo.get_by_slug(workspace_id, new_slug)
            if existing and existing.id != template_id:
                raise ConflictError(f"Template with title '{data.title}' already exists")
            update_dict["title"] = data.title
            update_dict["slug"] = new_slug

        if data.content is not None and data.content != template.content:
            update_dict["content"] = data.content
            update_dict["token_count"] = self._estimate_token_count(data.content)
            new_content = data.content
            create_new_version = True

        if data.schema_json is not None and data.schema_json != template.schema_json:
            update_dict["schema_json"] = data.schema_json
            new_schema = data.schema_json
            create_new_version = True

        if data.description is not None:
            update_dict["description"] = data.description
        if data.template_type is not None:
            update_dict["template_type"] = data.template_type
        if data.default_variables is not None:
            update_dict["default_variables"] = data.default_variables
        if data.is_pinned is not None:
            update_dict["is_pinned"] = data.is_pinned
        if data.metadata_json is not None:
            update_dict["metadata_json"] = data.metadata_json

        updated_template = await self.repo.update(template_id, update_dict)

        if create_new_version:
            next_version = updated_template.current_version + 1
            updated_template.current_version = next_version

            version_record = TemplateVersion(
                template_id=template_id,
                version_number=next_version,
                content=new_content,
                schema_json=new_schema,
                change_summary=data.change_summary or f"Updated to version {next_version}",
            )
            self.db.add(version_record)
            await self.db.flush()

            # Re-sync template variable linkages
            await self._sync_template_variables(template_id, new_content)

        return updated_template

    async def list_versions(self, workspace_id: str, template_id: str) -> list[TemplateVersion]:
        """List version history of a template."""
        await self.get_template(workspace_id, template_id)  # Validate exists
        return await self.repo.list_versions(template_id)

    async def delete_template(self, workspace_id: str, template_id: str) -> bool:
        """Soft delete a template."""
        await self.get_template(workspace_id, template_id)  # Validate exists
        return await self.repo.delete(template_id, soft=True)

    async def render(
        self,
        workspace_id: str,
        template_id: str,
        template_vars: dict[str, Any] | None = None,
        runtime_vars: dict[str, Any] | None = None,
    ) -> str:
        """Render prompt template with fully resolved variables."""
        template = await self.get_template(workspace_id, template_id)
        
        # Import dynamically to avoid circular import dependency
        from app.features.variables.service import VariableService
        var_service = VariableService(self.db)
        
        # Resolve variables with priority chain
        resolved = await var_service.resolve_variables(
            workspace_id=workspace_id,
            template_vars=template_vars,
            runtime_vars=runtime_vars,
        )
        
        # Extract primitive values
        context_vars = {name: info.value for name, info in resolved.items()}
        
        try:
            t = self.jinja_env.from_string(template.content)
            return t.render(**context_vars)
        except Exception as e:
            raise ValidationError(f"Render compilation error: {str(e)}")
