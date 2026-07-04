"""Template API and rendering engine integration tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_template_lifecycle_and_rendering(client: AsyncClient) -> None:
    """Verify template CRUD, versions auto-generation, Jinja2 variable detection, and rendering."""
    # 1. Create Workspace for scoping
    workspace_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Template Lab", "description": "Testing Jinja2"},
    )
    assert workspace_res.status_code == 201
    workspace = workspace_res.json()
    workspace_id = workspace["id"]

    # 2. Create prompt Template
    template_res = await client.post(
        f"/api/v1/templates?workspace_id={workspace_id}",
        json={
            "title": "Welcome Email",
            "content": "Hello {{ user_name }}, welcome to {{ workspace_name }}! Current date: {{ date }}.",
            "template_type": "prompt",
            "description": "Greeting email prompt template",
        },
    )
    assert template_res.status_code == 201
    template = template_res.json()
    template_id = template["id"]
    assert template["title"] == "Welcome Email"
    assert template["current_version"] == 1

    # 3. Check variable auto-sync registry
    # The variable user_name should be automatically created in the variables table
    vars_res = await client.get("/api/v1/variables")
    assert vars_res.status_code == 200
    variables = vars_res.json()
    var_names = [v["name"] for v in variables]
    assert "user_name" in var_names

    # 4. Preview Template Render
    preview_res = await client.post(
        f"/api/v1/templates/{template_id}/preview?workspace_id={workspace_id}",
        json={
            "template_vars": {"user_name": "Antigravity"},
            "runtime_vars": {},
        },
    )
    assert preview_res.status_code == 200
    preview = preview_res.json()
    
    # workspace_name (System) and date (System) should be auto-resolved
    assert "Hello Antigravity, welcome to Template Lab!" in preview["rendered"]
    assert "user_name" in preview["detected_variables"]
    assert "date" in preview["detected_variables"]

    # 5. Update template content and ensure version is incremented
    update_res = await client.patch(
        f"/api/v1/templates/{template_id}?workspace_id={workspace_id}",
        json={
            "content": "Hello {{ user_name }}! Glad you are here at {{ workspace_name }}.",
            "change_summary": "Simplify greeting wording",
        },
    )
    assert update_res.status_code == 200
    updated_template = update_res.json()
    assert updated_template["current_version"] == 2

    # 6. Fetch version history list
    versions_res = await client.get(
        f"/api/v1/templates/{template_id}/versions?workspace_id={workspace_id}"
    )
    assert versions_res.status_code == 200
    versions = versions_res.json()
    assert len(versions) == 2
    assert versions[0]["version_number"] == 2
    assert versions[1]["version_number"] == 1
