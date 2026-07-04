"""Variable API and engine integration tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_variable_engine_lifecycle(client: AsyncClient) -> None:
    """Verify variable CRUD, workspace override, and priority chain resolution."""
    # 1. Create Workspace for scoping
    workspace_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Variable Lab", "description": "Testing scoping"},
    )
    assert workspace_res.status_code == 201
    workspace = workspace_res.json()
    workspace_id = workspace["id"]

    # 2. Create Global Variable definition
    var_res = await client.post(
        "/api/v1/variables",
        json={
            "name": "api_endpoint",
            "display_name": "API Endpoint",
            "description": "Base URL for the API connection",
            "default_value": "https://api.global.com",
            "value_type": "text",
            "scope": "global",
        },
    )
    assert var_res.status_code == 201
    variable = var_res.json()
    variable_id = variable["id"]
    assert variable["name"] == "api_endpoint"

    # 3. Create Workspace-scoped Variable definition
    ws_var_res = await client.post(
        "/api/v1/variables",
        json={
            "name": "local_port",
            "display_name": "Local Port",
            "default_value": "8080",
            "value_type": "number",
            "scope": "workspace",
        },
    )
    assert ws_var_res.status_code == 201
    ws_variable = ws_var_res.json()
    assert ws_variable["scope"] == "workspace"

    # 4. Resolve variables without overrides
    resolve_res = await client.post(
        "/api/v1/variables/resolve",
        json={"workspace_id": workspace_id},
    )
    assert resolve_res.status_code == 200
    resolved = resolve_res.json()
    
    # Verify System variables are present
    assert "date" in resolved
    assert "time" in resolved
    assert resolved["workspace_name"]["value"] == "Variable Lab"

    # Verify Global and Workspace variables resolved to default values
    assert resolved["api_endpoint"]["value"] == "https://api.global.com"
    assert resolved["api_endpoint"]["is_override"] is False
    assert resolved["local_port"]["value"] == 8080  # Coerced to int number

    # 5. Save Workspace Override for the Global variable
    override_res = await client.post(
        f"/api/v1/variables/{variable_id}/workspaces/{workspace_id}/override",
        json={"value": "https://api.local.dev"},
    )
    assert override_res.status_code == 200
    override_data = override_res.json()
    assert override_data["value"] == "https://api.local.dev"

    # 6. Resolve variables WITH overrides, template variables and runtime overrides
    resolve_res2 = await client.post(
        "/api/v1/variables/resolve",
        json={
            "workspace_id": workspace_id,
            "template_vars": {"api_endpoint": "https://api.template.io", "extra_var": "hello"},
            "runtime_vars": {"api_endpoint": "https://api.runtime.net"},
        },
    )
    assert resolve_res2.status_code == 200
    resolved2 = resolve_res2.json()

    # Priority Chain: Runtime > Template > Workspace > Global > System
    # api_endpoint should resolve to runtime net
    assert resolved2["api_endpoint"]["value"] == "https://api.runtime.net"
    assert resolved2["api_endpoint"]["scope"] == "runtime"
    assert resolved2["api_endpoint"]["is_override"] is True

    # local_port should still resolve to 8080 (Workspace/Global level)
    assert resolved2["local_port"]["value"] == 8080

    # extra_var should resolve to template scope (hello)
    assert resolved2["extra_var"]["value"] == "hello"
    assert resolved2["extra_var"]["scope"] == "template"

    # 7. Delete variable definition
    del_res = await client.delete(f"/api/v1/variables/{variable_id}")
    assert del_res.status_code == 204
