"""Integration tests for AI Provider configurations (milestone M11)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_provider_management_workflow(client: AsyncClient) -> None:
    """Verify CRUD lifecycle, default toggle, key encryption, and deletion constraint for providers."""
    # 1. Initially, no custom providers
    list_res = await client.get("/api/v1/providers")
    assert list_res.status_code == 200
    providers = list_res.json()
    assert len(providers) == 0

    # 2. Create provider A
    prov_a_payload = {
        "name": "Azure East US",
        "provider_type": "azure_openai",
        "endpoint": "https://eastus-openai.openai.azure.com/",
        "api_version": "2024-12-01-preview",
        "deployment_chat": "gpt-4o",
        "deployment_chat_mini": "gpt-4o-mini",
        "deployment_embedding": "text-embedding-3",
        "api_key": "my-secret-azure-api-key",
        "is_active": 1,
    }
    create_res = await client.post("/api/v1/providers", json=prov_a_payload)
    assert create_res.status_code == 201
    prov_a = create_res.json()
    assert prov_a["name"] == "Azure East US"
    # Verify API key is masked in the response
    assert prov_a["api_key"] == "••••••••"
    # First provider should default to global default
    assert prov_a["is_default"] == 1
    id_a = prov_a["id"]

    # 3. Create provider B
    prov_b_payload = {
        "name": "Azure West Europe",
        "provider_type": "azure_openai",
        "endpoint": "https://westeurope-openai.openai.azure.com/",
        "api_version": "2024-12-01-preview",
        "api_key": "another-secret-key",
        "is_active": 1,
    }
    create_res2 = await client.post("/api/v1/providers", json=prov_b_payload)
    assert create_res2.status_code == 201
    prov_b = create_res2.json()
    assert prov_b["is_default"] == 0
    id_b = prov_b["id"]

    # 4. Swap default to B
    default_res = await client.post(f"/api/v1/providers/{id_b}/default")
    assert default_res.status_code == 200
    assert default_res.json()["is_default"] == 1

    # Check that A is no longer default
    res_a = await client.get(f"/api/v1/providers/{id_a}")
    assert res_a.json()["is_default"] == 0

    # 5. Prevent deleting the default provider (B)
    del_fail_res = await client.delete(f"/api/v1/providers/{id_b}")
    assert del_fail_res.status_code == 400

    # 6. Delete non-default provider (A)
    del_ok_res = await client.delete(f"/api/v1/providers/{id_a}")
    assert del_ok_res.status_code == 204

    # Verify A is not in active listings
    list_res2 = await client.get("/api/v1/providers")
    assert list_res2.status_code == 200
    assert len(list_res2.json()) == 1
    assert list_res2.json()[0]["id"] == id_b

    # 7. Test connection response shape (handles connect errors gracefully)
    test_res = await client.post(f"/api/v1/providers/{id_b}/test")
    assert test_res.status_code == 200
    data = test_res.json()
    assert "success" in data
    assert "message" in data
