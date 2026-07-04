"""Integration tests for Sprint 5B: Advanced AI features, Learning Engine, and Analytics (M36-M40)."""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.ai.client import AzureAIClient
from app.models import (
    Context,
    ContextDependency,
    ContextEmbedding,
    Conversation,
    LearningRecord,
    Message,
    PromptRun,
)


@pytest.fixture(autouse=True)
def mock_openai_endpoint(monkeypatch) -> None:
    """Mock the Azure OpenAI settings to bypass config checks during tests."""
    monkeypatch.setenv("POCKET_AZURE_OPENAI_ENDPOINT", "http://mock")
    monkeypatch.setenv("POCKET_AZURE_OPENAI_API_KEY", "mock_key")


@pytest.mark.asyncio
async def test_auto_tag_and_variables(client: AsyncClient) -> None:
    """Verify AI auto-tagging and variable extraction endpoints."""
    # 1. Test auto-tagging
    with patch("app.features.auto.router.AzureAIClient") as mock_client_cls:
        mock_inst = MagicMock(spec=AzureAIClient)
        mock_inst.chat_json = AsyncMock(return_value={"tags": ["math", "algebra", "education"]})
        mock_client_cls.return_value = mock_inst

        res = await client.post("/api/v1/auto/tag", json={"content": "Math rules"})
        assert res.status_code == 200
        assert "math" in res.json()["tags"]

    # 2. Test variable extraction
    with patch("app.features.auto.router.AzureAIClient") as mock_client_cls:
        mock_inst = MagicMock(spec=AzureAIClient)
        mock_inst.chat_json = AsyncMock(return_value={
            "variables": [
                {"name": "equation", "suggested_value": "2+2", "confidence": 0.95}
            ]
        })
        mock_client_cls.return_value = mock_inst

        res = await client.post("/api/v1/auto/extract-variables", json={"content": "Equation is 2+2"})
        assert res.status_code == 200
        assert res.json()["variables"][0]["name"] == "equation"


@pytest.mark.asyncio
async def test_duplicate_detection_and_merge(client: AsyncClient, db_session: AsyncSession) -> None:
    """Verify embedding-based duplicate context detection, merge, and dependency remapping."""
    # 1. Setup workspace & 2 duplicate contexts
    ws_res = await client.post("/api/v1/workspaces", json={"name": "Dedup Space"})
    ws_id = ws_res.json()["id"]

    c1 = Context(workspace_id=ws_id, title="Quantum A", slug="quantum-a", content="Intro to Quantum Physics", context_type="knowledge")
    c2 = Context(workspace_id=ws_id, title="Quantum B", slug="quantum-b", content="Intro to Quantum Physics duplicated", context_type="knowledge")
    c3 = Context(workspace_id=ws_id, title="Dependent", slug="dependent", content="Depends on Quantum A", context_type="instruction")
    
    db_session.add_all([c1, c2, c3])
    await db_session.flush()

    # Add embeddings for c1 and c2 (highly similar vectors)
    emb1 = ContextEmbedding(
        context_id=c1.id,
        model_name="text-embedding-3-large",
        dimensions=3,
        embedding=json.dumps([0.9, 0.1, 0.0]),
        content_hash="hash1",
    )
    emb2 = ContextEmbedding(
        context_id=c2.id,
        model_name="text-embedding-3-large",
        dimensions=3,
        embedding=json.dumps([0.89, 0.11, 0.0]),
        content_hash="hash2",
    )
    db_session.add_all([emb1, emb2])

    # Setup dependency edge (dependent -> c1)
    dep = ContextDependency(source_id=c3.id, target_id=c1.id, dependency_type="requires", weight=1.0)
    db_session.add(dep)
    await db_session.commit()

    # 2. Scan duplicates via API
    scan_res = await client.get(f"/api/v1/auto/duplicates?workspace_id={ws_id}&threshold=0.8")
    assert scan_res.status_code == 200
    dups = scan_res.json()
    assert len(dups) >= 1
    assert dups[0]["similarity"] > 0.90

    # 3. Merge contexts via API
    merge_payload = {
        "context_ids": [c1.id, c2.id],
        "target_title": "Quantum Physics Consolidated"
    }

    # Patch in router and dedup_service
    with patch("app.features.auto.router.AzureAIClient") as mock_router_client_cls, \
         patch("app.features.auto.dedup_service.AzureAIClient") as mock_service_client_cls:
        
        mock_inst = MagicMock(spec=AzureAIClient)
        mock_inst.chat_json = AsyncMock(return_value={"merged_content": "Intro to consolidated Quantum Physics"})
        
        mock_router_client_cls.return_value = mock_inst
        mock_service_client_cls.return_value = mock_inst

        merge_res = await client.post("/api/v1/auto/merge", json=merge_payload)
        assert merge_res.status_code == 200
        merged_ctx_data = merge_res.json()
        assert merged_ctx_data["title"] == "Quantum Physics Consolidated"

    # Verify old contexts archived
    await db_session.refresh(c1)
    stmt_c1 = select(Context).where(Context.id == c1.id)
    c1_db = (await db_session.execute(stmt_c1)).scalar()
    assert c1_db.is_archived == 1

    # Verify dependency re-mapped (dependent should now point to consolidated context)
    await db_session.refresh(dep)
    stmt_dep = select(ContextDependency).where(ContextDependency.source_id == c3.id)
    dep_db = (await db_session.execute(stmt_dep)).scalar()
    assert dep_db.target_id == merged_ctx_data["id"]


@pytest.mark.asyncio
async def test_learning_engine_api(client: AsyncClient, db_session: AsyncSession) -> None:
    """Verify that Learning Engine analyses chat and logs suggestions."""
    # 1. Setup conversation & dummy messages
    ws_res = await client.post("/api/v1/workspaces", json={"name": "Learning Space"})
    ws_id = ws_res.json()["id"]

    conv = Conversation(workspace_id=ws_id, title="Math Session", model="gpt-4.1")
    db_session.add(conv)
    await db_session.flush()

    m1 = Message(conversation_id=conv.id, role="user", content="How do I solve equations?")
    m2 = Message(conversation_id=conv.id, role="assistant", content="Explain variables first.")
    db_session.add_all([m1, m2])
    await db_session.commit()

    # 2. Trigger learning engine API
    with patch("app.ai.client.AzureAIClient") as mock_client_cls:
        mock_inst = MagicMock(spec=AzureAIClient)
        mock_inst.chat_json = AsyncMock(return_value={
            "quality_assessment": "good",
            "missing_contexts": [{"topic": "Variables Context", "impact": "minor"}],
            "successes": ["explained clearly"],
            "failures": [],
            "recommendations": ["add a variable context template"],
            "new_context_suggestions": [
                {
                    "title": "Algebra Variables Guide",
                    "content": "Explanation of x and y parameters.",
                    "type": "knowledge",
                    "reasoning": "User struggled with parameter bindings.",
                    "confidence": 0.85
                }
            ],
            "context_effectiveness": []
        })
        mock_client_cls.return_value = mock_inst

        learn_res = await client.post(f"/api/v1/conversations/{conv.id}/learn")
        assert learn_res.status_code == 200
        assert learn_res.json()["status"] == "success"

    # Verify LearningRecord & ContextCandidate created in DB
    stmt_rec = select(LearningRecord).where(LearningRecord.conversation_id == conv.id)
    rec_db = (await db_session.execute(stmt_rec)).scalar()
    assert rec_db is not None
    assert "Variables Context" in rec_db.missing_contexts


@pytest.mark.asyncio
async def test_analytics_dashboard_endpoints(client: AsyncClient, db_session: AsyncSession) -> None:
    """Verify aggregated overview, trends, top, and dead contexts APIs."""
    # 1. Setup workspace & sample PromptRuns/Contexts
    ws_res = await client.post("/api/v1/workspaces", json={"name": "Analytics Space"})
    ws_id = ws_res.json()["id"]

    # Active contexts
    c1 = Context(workspace_id=ws_id, title="C1", slug="c1", content="Text", context_type="knowledge", usage_count=10, last_used_at="2026-07-04T12:00:00Z")
    c2 = Context(workspace_id=ws_id, title="C2", slug="c2", content="Text", context_type="knowledge", usage_count=0, last_used_at=None)
    db_session.add_all([c1, c2])

    # PromptRuns
    pr1 = PromptRun(workspace_id=ws_id, user_input="hi", compiled_prompt="hi", model="gpt-4.1", total_tokens=100, prompt_tokens=80, completion_tokens=20, cost=0.002, validation_passed=1)
    db_session.add(pr1)
    await db_session.commit()

    # 2. Test Overview API
    res_over = await client.get(f"/api/v1/analytics/overview?workspace_id={ws_id}")
    assert res_over.status_code == 200
    data = res_over.json()
    assert data["total_contexts"] == 2
    assert data["total_prompts"] == 1
    assert data["total_tokens"] == 100
    assert data["total_cost"] == 0.002

    # 3. Test Trends API
    res_trend = await client.get(f"/api/v1/analytics/trends?workspace_id={ws_id}&days=7")
    assert res_trend.status_code == 200
    trends = res_trend.json()
    assert len(trends) == 7
    # One of the days should show tokens=100, cost=0.002
    assert any(t["tokens"] == 100 and t["cost"] == 0.002 for t in trends)

    # 4. Test Top Contexts
    res_top = await client.get(f"/api/v1/analytics/top-contexts?workspace_id={ws_id}")
    assert res_top.status_code == 200
    top = res_top.json()
    assert len(top) == 1
    assert top[0]["title"] == "C1"

    # 5. Test Dead Contexts
    res_dead = await client.get(f"/api/v1/analytics/dead-contexts?workspace_id={ws_id}")
    assert res_dead.status_code == 200
    dead = res_dead.json()
    assert len(dead) == 1
    assert dead[0]["title"] == "C2"
