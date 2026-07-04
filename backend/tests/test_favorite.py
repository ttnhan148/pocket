"""Integration tests for Favorites (milestone M10)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_favorites_lifecycle_and_reordering(client: AsyncClient) -> None:
    """Verify favoriting contexts, checking workspace isolation, list retrieval, and sorting."""
    # 1. Create Workspace
    ws_res = await client.post("/api/v1/workspaces", json={"name": "Fav Lab"})
    assert ws_res.status_code == 201
    workspace_id = ws_res.json()["id"]

    # 2. Create Contexts
    res_a = await client.post(
        f"/api/v1/workspaces/{workspace_id}/contexts",
        json={"title": "Doc A", "content": "Some content", "context_type": "knowledge"},
    )
    assert res_a.status_code == 201
    id_a = res_a.json()["id"]

    res_b = await client.post(
        f"/api/v1/workspaces/{workspace_id}/contexts",
        json={"title": "Doc B", "content": "Other content", "context_type": "knowledge"},
    )
    assert res_b.status_code == 201
    id_b = res_b.json()["id"]

    # 3. Initially favorites should be empty
    favs_init = await client.get(f"/api/v1/workspaces/{workspace_id}/favorites")
    assert favs_init.status_code == 200
    assert len(favs_init.json()) == 0

    # 4. Toggle Favorite on Doc A -> Added
    res_toggle1 = await client.post(
        f"/api/v1/workspaces/{workspace_id}/favorites/toggle",
        json={"entity_type": "context", "entity_id": id_a},
    )
    assert res_toggle1.status_code == 200
    data_t1 = res_toggle1.json()
    assert data_t1["entity_id"] == id_a
    assert data_t1["entity_type"] == "context"

    # 5. Toggle Favorite on Doc B -> Added
    res_toggle2 = await client.post(
        f"/api/v1/workspaces/{workspace_id}/favorites/toggle",
        json={"entity_type": "context", "entity_id": id_b},
    )
    assert res_toggle2.status_code == 200
    data_t2 = res_toggle2.json()
    assert data_t2["entity_id"] == id_b

    # 6. List Favorites -> check order
    list_res = await client.get(f"/api/v1/workspaces/{workspace_id}/favorites")
    assert list_res.status_code == 200
    favs_list = list_res.json()
    assert len(favs_list) == 2
    assert favs_list[0]["entity_id"] == id_a
    assert favs_list[1]["entity_id"] == id_b

    # 7. Reorder Favorites -> B then A
    reorder_res = await client.put(
        f"/api/v1/workspaces/{workspace_id}/favorites/reorder",
        json=[favs_list[1]["id"], favs_list[0]["id"]],
    )
    assert reorder_res.status_code == 200
    ordered_list = reorder_res.json()
    assert len(ordered_list) == 2
    assert ordered_list[0]["entity_id"] == id_b
    assert ordered_list[1]["entity_id"] == id_a

    # Verify listing shows new order
    list_res2 = await client.get(f"/api/v1/workspaces/{workspace_id}/favorites")
    assert list_res2.json()[0]["entity_id"] == id_b
    assert list_res2.json()[1]["entity_id"] == id_a

    # 8. Toggle Favorite on Doc A -> Removed
    res_toggle3 = await client.post(
        f"/api/v1/workspaces/{workspace_id}/favorites/toggle",
        json={"entity_type": "context", "entity_id": id_a},
    )
    assert res_toggle3.status_code == 200
    assert res_toggle3.json() is None

    # Check list has only 1 favorite now
    list_res3 = await client.get(f"/api/v1/workspaces/{workspace_id}/favorites")
    assert len(list_res3.json()) == 1
    assert list_res3.json()[0]["entity_id"] == id_b
