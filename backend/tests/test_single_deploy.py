"""Integration tests for Single-Deploy FastAPI Static Serving & Catch-all SPA Router (M46/M47)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_serve_frontend_index(client: AsyncClient) -> None:
    """Verify that root request / returns the index.html content."""
    res = await client.get("/")
    assert res.status_code == 200
    # Next.js export generates HTML starting with <!DOCTYPE html>
    assert "<!DOCTYPE html>" in res.text or "<html" in res.text


@pytest.mark.asyncio
async def test_serve_frontend_catchall(client: AsyncClient) -> None:
    """Verify client-side routes (e.g. /contexts) fallback to index.html."""
    res = await client.get("/contexts")
    assert res.status_code == 200
    assert "<!DOCTYPE html>" in res.text or "<html" in res.text


@pytest.mark.asyncio
async def test_serve_api_missing_remains_404(client: AsyncClient) -> None:
    """Verify that non-existent API routes (/api/v1/missing) return standard API 404 instead of index.html."""
    res = await client.get("/api/v1/missing-endpoint-abc")
    assert res.status_code == 404
    # Should return JSON detail, not HTML
    assert res.headers["content-type"].startswith("application/json")
    assert "detail" in res.json()
