"""Context dependencies integration tests (DAG verification & cycle validation)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dependency_lifecycle_and_cycle_rejection(client: AsyncClient) -> None:
    """Verify context dependencies addition, circular detection, and topological graph sorting."""
    # 1. Create Workspace
    ws_res = await client.post("/api/v1/workspaces", json={"name": "DAG Lab"})
    assert ws_res.status_code == 201
    workspace_id = ws_res.json()["id"]

    # 2. Create Context A
    res_a = await client.post(
        f"/api/v1/workspaces/{workspace_id}/contexts",
        json={"title": "Context A", "content": "Root context content", "context_type": "knowledge"},
    )
    assert res_a.status_code == 201
    id_a = res_a.json()["id"]

    # 3. Create Context B
    res_b = await client.post(
        f"/api/v1/workspaces/{workspace_id}/contexts",
        json={"title": "Context B", "content": "Depends on A", "context_type": "instruction"},
    )
    assert res_b.status_code == 201
    id_b = res_b.json()["id"]

    # 4. Create Context C
    res_c = await client.post(
        f"/api/v1/workspaces/{workspace_id}/contexts",
        json={"title": "Context C", "content": "Depends on B", "context_type": "persona"},
    )
    assert res_c.status_code == 201
    id_c = res_c.json()["id"]

    # 5. Add Dependency: B depends on A (B -> A)
    res_dep1 = await client.post(
        f"/api/v1/workspaces/{workspace_id}/contexts/{id_b}/dependencies",
        json={"target_id": id_a, "dependency_type": "requires", "weight": 1.0},
    )
    assert res_dep1.status_code == 201

    # 6. Add Dependency: C depends on B (C -> B)
    res_dep2 = await client.post(
        f"/api/v1/workspaces/{workspace_id}/contexts/{id_c}/dependencies",
        json={"target_id": id_b, "dependency_type": "extends", "weight": 2.0},
    )
    assert res_dep2.status_code == 201

    # 7. Try adding self-reference dependency: A depends on A (A -> A) -> Validation error
    res_self = await client.post(
        f"/api/v1/workspaces/{workspace_id}/contexts/{id_a}/dependencies",
        json={"target_id": id_a},
    )
    assert res_self.status_code == 422

    # 8. Try causing circular dependency: A depends on C (A -> C)
    # The current graph: C depends on B, B depends on A (C -> B -> A).
    # If A depends on C, we form a cycle: A -> C -> B -> A -> Validation error
    res_cycle = await client.post(
        f"/api/v1/workspaces/{workspace_id}/contexts/{id_a}/dependencies",
        json={"target_id": id_c},
    )
    assert res_cycle.status_code == 422
    assert "Circular dependency detected" in res_cycle.json()["detail"]

    # 9. Get graph and verify topological sorting order
    # Independence / Leaf nodes should go first. C depends on B depends on A.
    # So resolution order should evaluate A first, then B, then C: [id_a, id_b, id_c]
    res_graph = await client.get(f"/api/v1/workspaces/{workspace_id}/dependency-graph")
    assert res_graph.status_code == 200
    graph_data = res_graph.json()
    assert len(graph_data["nodes"]) == 3
    assert len(graph_data["edges"]) == 2
    assert graph_data["topological_order"] == [id_a, id_b, id_c]

    # 10. Remove dependency relationship
    res_del = await client.delete(f"/api/v1/workspaces/{workspace_id}/contexts/{id_c}/dependencies/{id_b}")
    assert res_del.status_code == 204

    # Verify edge count is now 1
    res_graph2 = await client.get(f"/api/v1/workspaces/{workspace_id}/dependency-graph")
    assert len(res_graph2.json()["edges"]) == 1
