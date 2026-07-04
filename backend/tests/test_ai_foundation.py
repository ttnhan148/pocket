"""Unit and integration tests for AI Foundation & Search (M17-M22)."""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.ai.client import AzureAIClient, ChatResult
from app.ai.embeddings import EmbeddingService, cosine_similarity
from app.ai.pipeline.search import prepare_fts_query, normalize_bm25
from app.ai.pipeline.ranking import RankingEngine, RetrievalResult


def test_cosine_similarity() -> None:
    """Verify that cosine similarity computes correct values for known vectors."""
    # Test identical vectors (similarity = 1.0)
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert pytest.approx(cosine_similarity(v1, v2)) == 1.0

    # Test orthogonal vectors (similarity = 0.0)
    v3 = [0.0, 1.0, 0.0]
    assert pytest.approx(cosine_similarity(v1, v3)) == 0.0

    # Test opposite vectors (similarity = -1.0)
    v4 = [-1.0, 0.0, 0.0]
    assert pytest.approx(cosine_similarity(v1, v4)) == -1.0

    # Test normal vectors
    v5 = [3.0, 4.0]
    v6 = [4.0, 3.0]
    # Dot product: 12 + 12 = 24. Norms: 5, 5. Similarity = 24 / 25 = 0.96
    assert pytest.approx(cosine_similarity(v5, v6)) == 0.96


def test_prepare_fts_query() -> None:
    """Verify FTS5 query builder sanitizes input correctly."""
    assert prepare_fts_query("hello world") == "hello AND world*"
    assert prepare_fts_query("hello-world! @test") == "hello AND world AND test*"
    assert prepare_fts_query("   ") == ""


def test_normalize_bm25() -> None:
    """Verify BM25 normalization scales appropriately."""
    assert normalize_bm25(0.0) == 0.0
    assert normalize_bm25(1.0) == 0.0
    assert normalize_bm25(-5.0) == 5.0 / 6.0
    assert normalize_bm25(-9.0) == 0.9


@pytest.mark.asyncio
async def test_azure_ai_client_cost_computation() -> None:
    """Verify Azure AI client cost logic executes properly."""
    res = ChatResult(
        content="Hello!",
        finish_reason="stop",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        model="gpt-4.1-mini",
    )
    # input rate: 0.15/1M, output: 0.60/1M
    expected_cost = (100 * 0.15 / 1_000_000) + (50 * 0.60 / 1_000_000)
    assert pytest.approx(res.compute_cost()) == expected_cost


@pytest.mark.asyncio
async def test_ranking_engine() -> None:
    """Verify ranking engine scores contexts based on 9-factor inputs."""
    engine = RankingEngine()
    
    # Mock context model
    ctx = MagicMock()
    ctx.id = "ctx-1"
    ctx.priority = 80
    ctx.usage_count = 5
    ctx.last_used_at = None
    ctx.workspace_id = "ws-1"
    ctx.confidence = 0.9
    ctx.quality_score = 0.8

    retrieval_res = RetrievalResult(
        context=ctx,
        fts_score=0.7,
        fuzzy_score=0.5,
        semantic_score=0.8,
        metadata_score=0.6,
        final_score=0.75,
    )

    ranked = engine.rank(
        results=[retrieval_res],
        workspace_id="ws-1",
        favorites={"ctx-1"},
        dependency_weights={"ctx-1": 1.0},
    )

    assert len(ranked) == 1
    item = ranked[0]
    assert item.context.id == "ctx-1"
    assert item.score_breakdown["priority"] == 0.8
    assert item.score_breakdown["favorite"] == 1.0
    assert item.score_breakdown["workspace"] == 1.0
    assert item.score_breakdown["quality"] == 0.8
    assert item.score > 0.0


@pytest.mark.asyncio
async def test_search_api_lifecycle(client: AsyncClient) -> None:
    """Verify search API router handles queries and returns consolidated results."""
    # 1. Create Workspace
    workspace_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Search Lab", "description": "Testing search endpoints"},
    )
    assert workspace_res.status_code == 201
    workspace = workspace_res.json()
    workspace_id = workspace["id"]

    # 2. Call search on empty workspace (should return empty results list)
    search_res = await client.get(
        f"/api/v1/search?workspace_id={workspace_id}&q=testing"
    )
    assert search_res.status_code == 200
    data = search_res.json()
    assert "results" in data
    assert len(data["results"]) == 0
