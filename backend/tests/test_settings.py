"""Integration tests for global settings (milestone M11)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_global_settings_endpoints(client: AsyncClient) -> None:
    """Verify that settings can be retrieved, updated, and validated properly."""
    # 1. Fetch initial settings (seeded)
    get_res = await client.get("/api/v1/settings")
    assert get_res.status_code == 200
    settings = get_res.json()
    assert len(settings) >= 7

    # Verify a few default values
    auto_embed_setting = next((s for s in settings if s["key"] == "auto_embed"), None)
    assert auto_embed_setting is not None
    assert auto_embed_setting["value"] == "true"
    assert auto_embed_setting["value_type"] == "boolean"

    # 2. Get single setting
    single_res = await client.get("/api/v1/settings/auto_embed")
    assert single_res.status_code == 200
    assert single_res.json()["value"] == "true"

    # Get non-existent setting
    non_existent = await client.get("/api/v1/settings/unknown_key_xyz")
    assert non_existent.status_code == 404

    # 3. Bulk update valid settings
    update_res = await client.put(
        "/api/v1/settings",
        json={
            "updates": [
                {"key": "auto_embed", "value": "false"},
                {"key": "token_limit", "value": "200000"},
            ]
        },
    )
    assert update_res.status_code == 200
    updated_settings = update_res.json()

    updated_auto_embed = next((s for s in updated_settings if s["key"] == "auto_embed"), None)
    assert updated_auto_embed is not None
    assert updated_auto_embed["value"] == "false"

    # 4. Try updating with invalid values (enforcing validation)
    # Invalid boolean
    bad_bool_res = await client.put(
        "/api/v1/settings",
        json={
            "updates": [
                {"key": "auto_embed", "value": "not_a_boolean"},
            ]
        },
    )
    assert bad_bool_res.status_code == 400

    # Invalid number
    bad_num_res = await client.put(
        "/api/v1/settings",
        json={
            "updates": [
                {"key": "token_limit", "value": "abc"},
            ]
        },
    )
    assert bad_num_res.status_code == 400

    # Unknown key
    bad_key_res = await client.put(
        "/api/v1/settings",
        json={
            "updates": [
                {"key": "unknown_key_xyz", "value": "some_value"},
            ]
        },
    )
    assert bad_key_res.status_code == 404
