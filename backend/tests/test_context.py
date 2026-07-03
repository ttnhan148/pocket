"""Context API integration tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_context_full_lifecycle_and_search(client: AsyncClient) -> None:
    """Verify context creation, version bumping, listing, FTS search, and soft deletion."""
    # 1. Prepare Workspace
    ws_payload = {"name": "Pocket Lab", "description": "Context and Prompt Testing"}
    ws_response = await client.post("/api/v1/workspaces", json=ws_payload)
    assert ws_response.status_code == 201
    workspace_id = ws_response.json()["id"]

    # 2. Create Context (V1)
    context_payload = {
        "title": "System Prompt Constitutional Guide",
        "content": "Rule 1: Be explicit. Rule 2: Keep models constraint-bound.",
        "context_type": "instruction",
        "priority": 80,
        "confidence": 0.95,
        "metadata_json": {"format": "standard"},
    }
    response = await client.post(f"/api/v1/workspaces/{workspace_id}/contexts", json=context_payload)
    assert response.status_code == 201
    ctx_data = response.json()
    assert ctx_data["title"] == "System Prompt Constitutional Guide"
    assert ctx_data["slug"] == "system-prompt-constitutional-guide"
    assert ctx_data["current_version"] == 1
    assert ctx_data["token_count"] > 0
    context_id = ctx_data["id"]

    # 3. Create context with duplicate title to test slug collision resolution
    context_dup = {
        "title": "System Prompt Constitutional Guide",  # Duplicate title
        "content": "Different content.",
        "context_type": "instruction",
    }
    response_dup = await client.post(f"/api/v1/workspaces/{workspace_id}/contexts", json=context_dup)
    assert response_dup.status_code == 201
    assert response_dup.json()["slug"] == "system-prompt-constitutional-guide-2"

    # 4. Get Context Details
    response = await client.get(f"/api/v1/workspaces/{workspace_id}/contexts/{context_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "System Prompt Constitutional Guide"

    # 5. List Contexts
    response = await client.get(f"/api/v1/workspaces/{workspace_id}/contexts")
    assert response.status_code == 200
    contexts = response.json()
    assert len(contexts) >= 2

    # 6. Update Context (Trigger V2 version bump)
    update_payload = {
        "title": "Constitutional Prompt Guide Revised",  # Title change
        "content": "Rule 1: Be explicit. Rule 2: Keep models constraint-bound. Rule 3: Always verify.",  # Content change
    }
    response = await client.put(f"/api/v1/workspaces/{workspace_id}/contexts/{context_id}", json=update_payload)
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["title"] == "Constitutional Prompt Guide Revised"
    assert updated_data["current_version"] == 2  # Current version bumped
    assert updated_data["slug"] == "constitutional-prompt-guide-revised"  # Slug updated

    # 7. Get Version History
    response = await client.get(f"/api/v1/workspaces/{workspace_id}/contexts/{context_id}/versions")
    assert response.status_code == 200
    versions = response.json()
    assert len(versions) == 2
    assert versions[0]["version_number"] == 2
    assert versions[1]["version_number"] == 1

    # 8. Full-Text Search (FTS5)
    # Search for "constraint-bound" (matches guide)
    response = await client.get(f"/api/v1/workspaces/{workspace_id}/contexts/search", params={"q": "constraint-bound"})
    assert response.status_code == 200
    search_results = response.json()
    assert len(search_results) == 1
    assert search_results[0]["id"] == context_id

    # Search for a term that does not exist
    response = await client.get(f"/api/v1/workspaces/{workspace_id}/contexts/search", params={"q": "nonexistentterm"})
    assert response.status_code == 200
    assert len(response.json()) == 0

    # 9. Delete Context
    response = await client.delete(f"/api/v1/workspaces/{workspace_id}/contexts/{context_id}")
    assert response.status_code == 204

    # Verify retrieved context is soft deleted (returns 404)
    response = await client.get(f"/api/v1/workspaces/{workspace_id}/contexts/{context_id}")
    assert response.status_code == 404
