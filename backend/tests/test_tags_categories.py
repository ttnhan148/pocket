"""Tags and Categories integration tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_tags_and_categories_lifecycle(client: AsyncClient) -> None:
    """Verify CRUD and hierarchical rules for tags and categories."""
    # 1. Create Workspace
    ws_response = await client.post("/api/v1/workspaces", json={"name": "Folder Lab"})
    assert ws_response.status_code == 201
    workspace_id = ws_response.json()["id"]

    # ── TAGS TESTS ────────────────────────────────────────────────────────

    # 2. Create Tag
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/tags",
        json={"name": "FastAPI", "color": "#009688"},
    )
    assert response.status_code == 201
    tag_data = response.json()
    assert tag_data["name"] == "FastAPI"
    assert tag_data["slug"] == "fastapi"
    tag_id = tag_data["id"]

    # 3. Create Duplicate Tag (should return the same tag)
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/tags",
        json={"name": "FastAPI", "color": "#FF0000"},
    )
    assert response.status_code == 201
    assert response.json()["id"] == tag_id

    # 4. List Tags
    response = await client.get(f"/api/v1/workspaces/{workspace_id}/tags")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # 5. Delete Tag
    response = await client.delete(f"/api/v1/workspaces/{workspace_id}/tags/{tag_id}")
    assert response.status_code == 204

    # ── CATEGORIES TESTS ──────────────────────────────────────────────────

    # 6. Create Category Folder A (Root)
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/categories",
        json={"name": "Folder A", "description": "Top-level category"},
    )
    assert response.status_code == 201
    cat_a_id = response.json()["id"]

    # 7. Create Category Folder B (Nested under A)
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/categories",
        json={"name": "Folder B", "parent_id": cat_a_id},
    )
    assert response.status_code == 201
    cat_b_id = response.json()["id"]

    # 8. Create Category Folder C (Nested under B)
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/categories",
        json={"name": "Folder C", "parent_id": cat_b_id},
    )
    assert response.status_code == 201
    cat_c_id = response.json()["id"]

    # 9. Verify tree structure
    response = await client.get(f"/api/v1/workspaces/{workspace_id}/categories")
    assert response.status_code == 200
    tree = response.json()
    assert len(tree) == 1
    assert tree[0]["id"] == cat_a_id
    assert len(tree[0]["children"]) == 1
    assert tree[0]["children"][0]["id"] == cat_b_id
    assert len(tree[0]["children"][0]["children"]) == 1
    assert tree[0]["children"][0]["children"][0]["id"] == cat_c_id

    # 10. Reconstruct parent to cause hierarchical cycle (rejection check)
    # Trying to make A (parent) a child of C (descendant) -> Should trigger ValidationError
    response = await client.put(
        f"/api/v1/workspaces/{workspace_id}/categories/{cat_a_id}",
        json={"parent_id": cat_c_id},
    )
    assert response.status_code == 422
    assert "cycle detected" in response.json()["detail"]

    # 11. Delete Parent category unlinks children
    response = await client.delete(f"/api/v1/workspaces/{workspace_id}/categories/{cat_a_id}")
    assert response.status_code == 204

    # Verify B is now a root category
    response = await client.get(f"/api/v1/workspaces/{workspace_id}/categories")
    assert response.status_code == 200
    tree = response.json()
    assert len(tree) == 1
    assert tree[0]["id"] == cat_b_id
    assert tree[0]["parent_id"] is None
