"""Workspace API integration tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_workspace_full_lifecycle(client: AsyncClient) -> None:
    """Verify create, list, default toggle, update, and delete workspace endpoints."""
    # 1. Create Workspace
    payload = {
        "name": "Project Alpha",
        "description": "Primary development workspace",
        "icon": "folder",
        "color": "#3B82F6",
        "metadata_json": {"team": "Engineers"},
    }
    response = await client.post("/api/v1/workspaces", json=payload)
    assert response.status_code == 201
    created_data = response.json()
    assert created_data["name"] == "Project Alpha"
    assert created_data["slug"] == "project-alpha"
    assert created_data["is_default"] == 1  # First workspace should automatically be default
    workspace_id = created_data["id"]

    # 2. Get Workspace by ID
    response = await client.get(f"/api/v1/workspaces/{workspace_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Project Alpha"

    # 3. Create a second workspace (should test slug duplication resolution)
    payload_dup = {
        "name": "Project Alpha!",  # Different name, but same slugify output
        "description": "Secondary development workspace",
    }
    response = await client.post("/api/v1/workspaces", json=payload_dup)
    assert response.status_code == 201
    second_data = response.json()
    assert second_data["name"] == "Project Alpha!"
    assert second_data["slug"] == "project-alpha-2"  # Suffix appended
    assert second_data["is_default"] == 0  # Second workspace is not default by default
    second_id = second_data["id"]

    # 4. List workspaces
    response = await client.get("/api/v1/workspaces")
    assert response.status_code == 200
    workspaces = response.json()
    assert len(workspaces) >= 2

    # 5. Toggle default workspace
    response = await client.put(f"/api/v1/workspaces/{second_id}/default")
    assert response.status_code == 200
    updated_second = response.json()
    assert updated_second["is_default"] == 1

    # Verify original workspace is no longer default
    response = await client.get(f"/api/v1/workspaces/{workspace_id}")
    assert response.json()["is_default"] == 0

    # 6. Update workspace
    update_payload = {
        "name": "Project Alpha Renamed",
        "description": "New description",
        "color": "#FF0000",
    }
    response = await client.put(f"/api/v1/workspaces/{workspace_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Project Alpha Renamed"
    assert response.json()["color"] == "#FF0000"

    # 7. Fail to delete default workspace
    response = await client.delete(f"/api/v1/workspaces/{second_id}")
    assert response.status_code == 422  # ValidationError due to is_default = 1
    assert "Cannot delete the default workspace" in response.json()["detail"]

    # 8. Successfully delete non-default workspace
    response = await client.delete(f"/api/v1/workspaces/{workspace_id}")
    assert response.status_code == 204

    # Verify it is deleted (404 Not Found)
    response = await client.get(f"/api/v1/workspaces/{workspace_id}")
    assert response.status_code == 404
