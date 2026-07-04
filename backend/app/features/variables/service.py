"""Variable Service layer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.core.exceptions import ConflictError, NotFoundError
from app.core.service import BaseService
from app.features.variables.repository import VariableRepository
from app.features.variables.schemas import VariableCreate, VariableUpdate, VariableResolveResponse
from app.models import Variable, WorkspaceVariable, Workspace


class VariableService(BaseService):
    """Business logic service for managing Variables and Variable Resolution."""

    def __init__(self, db: Any) -> None:
        super().__init__(db)
        self.repo = VariableRepository(db)

    async def create_variable(self, data: VariableCreate) -> Variable:
        """Create a new variable, ensuring uniqueness of the name within its scope."""
        # System reserved names check
        reserved_names = {"date", "time", "datetime", "workspace_id", "workspace_name", "workspace_slug", "active_provider"}
        if data.name.lower() in reserved_names:
            raise ValidationError(f"Variable name '{data.name}' is reserved for system variables")

        # Check name conflict within the scope
        existing = await self.repo.get_by_name(data.name, data.scope)
        if existing:
            raise ConflictError(f"Variable '{data.name}' already exists in scope '{data.scope}'")

        variable = Variable(
            name=data.name,
            display_name=data.display_name,
            description=data.description,
            default_value=data.default_value,
            value_type=data.value_type,
            options=data.options,
            is_required=data.is_required,
            is_system=data.is_system,
            scope=data.scope,
            sort_order=data.sort_order,
        )
        return await self.repo.create(variable)

    async def get_variable(self, id_: str) -> Variable:
        """Retrieve a variable by its ID, raising NotFoundError if not found."""
        return await self.repo.get_or_raise(id_)

    async def list_variables(self, scope: str | None = None) -> list[Variable]:
        """List variables, optionally filtered by scope."""
        return await self.repo.list_variables(scope)

    async def update_variable(self, id_: str, data: VariableUpdate) -> Variable:
        """Update fields of an existing Variable."""
        variable = await self.get_variable(id_)

        update_dict: dict[str, Any] = {}
        if data.display_name is not None:
            update_dict["display_name"] = data.display_name
        if data.description is not None:
            update_dict["description"] = data.description
        if data.default_value is not None:
            update_dict["default_value"] = data.default_value
        if data.value_type is not None:
            update_dict["value_type"] = data.value_type
        if data.options is not None:
            update_dict["options"] = data.options
        if data.is_required is not None:
            update_dict["is_required"] = data.is_required
        if data.sort_order is not None:
            update_dict["sort_order"] = data.sort_order

        return await self.repo.update(id_, update_dict)

    async def delete_variable(self, id_: str) -> bool:
        """Soft delete variable by ID."""
        variable = await self.get_variable(id_)
        if variable.is_system:
            raise ConflictError("Cannot delete system-defined variables")
        return await self.repo.delete(id_, soft=True)

    async def save_workspace_override(self, workspace_id: str, variable_id: str, value: str | None) -> WorkspaceVariable:
        """Save a workspace override value for a variable."""
        # Verify workspace exists
        stmt = select(Workspace).where(Workspace.id == workspace_id, Workspace.deleted_at.is_(None))
        workspace = (await self.db.execute(stmt)).scalar()
        if not workspace:
            raise NotFoundError("Workspace", workspace_id)

        # Verify variable exists
        variable = await self.get_variable(variable_id)

        return await self.repo.save_workspace_override(workspace_id, variable_id, value)

    def _parse_value(self, value_str: str | None, value_type: str) -> Any:
        """Parse raw string database values to respective python types."""
        if value_str is None:
            return None

        try:
            if value_type == "number":
                if "." in value_str:
                    return float(value_str)
                return int(value_str)
            elif value_type == "boolean":
                return value_str.lower() in ("true", "1", "yes", "t")
            elif value_type == "json":
                return json.loads(value_str)
            return value_str
        except Exception:
            return value_str

    async def resolve_variables(
        self,
        workspace_id: str,
        template_vars: dict[str, Any] | None = None,
        runtime_vars: dict[str, Any] | None = None,
    ) -> dict[str, VariableResolveResponse]:
        """
        Resolve all variables based on priority chain:
        System -> Global -> Workspace-scoped -> Template-scoped -> Runtime.
        """
        # 1. Fetch workspace to resolve system variables
        stmt = select(Workspace).where(Workspace.id == workspace_id, Workspace.deleted_at.is_(None))
        workspace = (await self.db.execute(stmt)).scalar()
        if not workspace:
            raise NotFoundError("Workspace", workspace_id)

        now = datetime.now(timezone.utc)
        resolved: dict[str, VariableResolveResponse] = {}

        # ── SYSTEM SCOPE (Lowest priority) ─────────────────────────────────
        system_defaults = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "datetime": now.isoformat(),
            "workspace_id": workspace.id,
            "workspace_name": workspace.name,
            "workspace_slug": workspace.slug,
        }

        for k, v in system_defaults.items():
            resolved[k] = VariableResolveResponse(
                name=k,
                value=v,
                value_type="text",
                scope="system",
                source="System default",
                is_override=False,
            )

        # ── GLOBAL & WORKSPACE SCOPE (From variables registry) ──────────────
        all_variables = await self.repo.list_variables()
        overrides = await self.repo.get_workspace_overrides(workspace_id)
        override_map = {ov.variable_id: ov.value for ov in overrides}

        for var in all_variables:
            var_value = var.default_value
            scope = var.scope
            source = f"Global variable default"
            is_override = False

            # Check for workspace specific override
            if var.id in override_map and override_map[var.id] is not None:
                var_value = override_map[var.id]
                source = f"Workspace variable override ({workspace.name})"
                is_override = True

            parsed_val = self._parse_value(var_value, var.value_type)

            resolved[var.name] = VariableResolveResponse(
                name=var.name,
                value=parsed_val,
                value_type=var.value_type,
                scope=scope,
                source=source,
                is_override=is_override,
            )

        # ── TEMPLATE SCOPE (Overrides database values) ──────────────────────
        if template_vars:
            for k, v in template_vars.items():
                resolved[k] = VariableResolveResponse(
                    name=k,
                    value=v,
                    value_type="text" if not isinstance(v, (int, float, bool, dict, list)) else type(v).__name__,
                    scope="template",
                    source="Template variable override",
                    is_override=True,
                )

        # ── RUNTIME SCOPE (Highest priority) ─────────────────────────────────
        if runtime_vars:
            for k, v in runtime_vars.items():
                resolved[k] = VariableResolveResponse(
                    name=k,
                    value=v,
                    value_type="text" if not isinstance(v, (int, float, bool, dict, list)) else type(v).__name__,
                    scope="runtime",
                    source="Runtime prompt execution value",
                    is_override=True,
                )

        return resolved
