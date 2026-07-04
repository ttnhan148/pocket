"""Integration tests for Phase 6: Advanced AI, Journals, and Import/Export."""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import Settings
from app.ai.client import AzureAIClient
from app.ai.pipeline.retrieval import RetrievalEngine
from app.ai.pipeline.ranking import RankedContext
from app.models import Context, Tag, PromptRun, AIJob
from app.features.jobs.runner import run_prompt_benchmark, run_context_health_check


@pytest.fixture(autouse=True)
def mock_openai_endpoint(monkeypatch) -> None:
    """Mock the Azure OpenAI settings to bypass config checks during tests."""
    monkeypatch.setenv("POCKET_AZURE_OPENAI_ENDPOINT", "http://mock")
    monkeypatch.setenv("POCKET_AZURE_OPENAI_API_KEY", "mock_key")


@pytest.mark.asyncio
async def test_generate_context_api(client: AsyncClient, db_session: AsyncSession) -> None:
    """Verify that the AI context generation API constructs the prompt and persists context and tags."""
    # 1. Setup workspace
    ws_res = await client.post("/api/v1/workspaces", json={"name": "Gen Space"})
    ws_id = ws_res.json()["id"]

    # 2. Mock AzureAIClient.chat_json
    with patch("app.ai.client.AzureAIClient") as mock_client_cls:
        mock_inst = MagicMock(spec=AzureAIClient)
        mock_inst.chat_json = AsyncMock(return_value={
            "title": "Quantum Physics Basics",
            "content": "Intro to quantum mechanics.",
            "context_type": "knowledge",
            "tags": ["physics", "quantum", "science"]
        })
        mock_client_cls.return_value = mock_inst

        # 3. Call API
        res = await client.post(
            f"/api/v1/workspaces/{ws_id}/contexts/generate",
            json={"description": "Write a physics context about quantum basics"}
        )
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Quantum Physics Basics"
        assert data["context_type"] == "knowledge"
        
        # Verify tags created and linked
        tags = [t["name"] for t in data["tags"]]
        assert "physics" in tags
        assert "quantum" in tags
        assert "science" in tags

        # Verify persisted in database
        stmt = select(Context).options(selectinload(Context.tags)).where(Context.id == data["id"])
        ctx_db = (await db_session.execute(stmt)).scalar()
        assert ctx_db is not None
        assert len(ctx_db.tags) == 3


@pytest.mark.asyncio
async def test_suggest_contexts_api(client: AsyncClient, db_session: AsyncSession) -> None:
    """Verify that the context suggestion API invokes retrieval engine and excludes already selected contexts."""
    # 1. Setup workspace & 3 contexts
    ws_res = await client.post("/api/v1/workspaces", json={"name": "Suggest Space"})
    ws_id = ws_res.json()["id"]

    c1 = Context(workspace_id=ws_id, title="Quantum A", slug="quantum-a", content="Text", context_type="knowledge")
    c2 = Context(workspace_id=ws_id, title="Quantum B", slug="quantum-b", content="Text", context_type="knowledge")
    c3 = Context(workspace_id=ws_id, title="Math basics", slug="math-basics", content="Text", context_type="knowledge")
    db_session.add_all([c1, c2, c3])
    await db_session.commit()

    # 2. Mock RetrievalEngine.search
    # It should return ranked contexts
    ranked_1 = RankedContext(context=c1, score=0.9, score_breakdown={})
    ranked_2 = RankedContext(context=c2, score=0.8, score_breakdown={})
    ranked_3 = RankedContext(context=c3, score=0.1, score_breakdown={})

    with patch("app.features.context.ai_service.RetrievalEngine") as mock_engine_cls:
        mock_inst = MagicMock(spec=RetrievalEngine)
        mock_inst.search = AsyncMock(return_value=[ranked_1, ranked_2, ranked_3])
        mock_engine_cls.return_value = mock_inst

        # Call suggest API excluding c1
        res = await client.post(
            f"/api/v1/workspaces/{ws_id}/contexts/suggest",
            json={
                "draft_content": "quantum prompt draft",
                "already_selected_ids": [c1.id],
                "limit": 2
            }
        )
        assert res.status_code == 200
        suggestions = res.json()
        
        # Should only contain c2 (since c1 is excluded and limit is 2, though c3 is also there but lower score)
        assert len(suggestions) == 2
        assert suggestions[0]["id"] == c2.id
        assert suggestions[1]["id"] == c3.id


@pytest.mark.asyncio
async def test_prompt_benchmark_api(client: AsyncClient, db_session: AsyncSession) -> None:
    """Verify triggering prompt benchmark job and fetching status/results."""
    # 1. Setup workspace & PromptRun
    ws_res = await client.post("/api/v1/workspaces", json={"name": "Bench Space"})
    ws_id = ws_res.json()["id"]

    pr = PromptRun(
        workspace_id=ws_id,
        user_input="explain quantum physics simply",
        compiled_prompt="Explain quantum physics with easy terms",
        model="gpt-4.1",
        total_tokens=10,
        prompt_tokens=5,
        completion_tokens=5,
        cost=0.0001,
        validation_passed=1,
    )
    db_session.add(pr)
    await db_session.commit()

    # 2. Call benchmark route
    res = await client.post(f"/api/v1/prompts/{pr.id}/benchmark")
    assert res.status_code == 202
    job_id = res.json()["job_id"]
    assert res.json()["status"] == "pending"

    # 3. Force run the background runner synchronously for testing
    with patch.object(AzureAIClient, "chat_json", new_callable=AsyncMock) as mock_chat_json:
        mock_chat_json.return_value = {
            "alternative_prompt": "Explain quantum physics in simpler words",
            "original_scores": {"clarity": 0.8, "specificity": 0.7, "completeness": 0.8, "consistency": 0.9, "efficiency": 0.6},
            "alternative_scores": {"clarity": 0.9, "specificity": 0.8, "completeness": 0.9, "consistency": 0.9, "efficiency": 0.8},
            "comparison_summary": "Alternative is slightly cleaner."
        }

        await run_prompt_benchmark(job_id, pr.id)

    # 4. Fetch job status & results
    res_job = await client.get(f"/api/v1/jobs/{job_id}")
    assert res_job.status_code == 200
    job_data = res_job.json()
    assert job_data["status"] == "completed"
    assert len(job_data["results"]) == 1
    assert job_data["results"][0]["result_type"] == "prompt_benchmark"
    assert "alternative_prompt" in job_data["results"][0]["result_data"]


@pytest.mark.asyncio
async def test_weekly_review_api(client: AsyncClient, db_session: AsyncSession) -> None:
    """Verify compilation of weekly review analytics and recommendations."""
    # 1. Setup workspace & PromptRuns
    ws_res = await client.post("/api/v1/workspaces", json={"name": "Review Space"})
    ws_id = ws_res.json()["id"]

    # Active contexts
    c1 = Context(workspace_id=ws_id, title="Quantum Intro", slug="quantum-intro", content="Text", context_type="knowledge", usage_count=50)
    c2 = Context(workspace_id=ws_id, title="Stale Guide", slug="stale-guide", content="Text", context_type="knowledge", usage_count=0, last_used_at=None)
    db_session.add_all([c1, c2])

    pr = PromptRun(
        workspace_id=ws_id,
        user_input="test input",
        compiled_prompt="test compiled",
        model="gpt-4.1",
        total_tokens=1000,
        prompt_tokens=500,
        completion_tokens=500,
        cost=2.50, # High cost to trigger cost recommendation
        validation_passed=1,
    )
    db_session.add(pr)
    await db_session.commit()

    # 2. Call weekly-review endpoint
    res = await client.get(f"/api/v1/analytics/weekly-review?workspace_id={ws_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["total_prompts"] == 1
    assert data["total_tokens"] == 1000
    assert data["total_cost"] == 2.50
    assert len(data["top_contexts"]) == 1
    assert data["top_contexts"][0]["title"] == "Quantum Intro"
    assert len(data["dead_contexts"]) == 1
    assert data["dead_contexts"][0]["title"] == "Stale Guide"
    
    # Verify recommendations compiled
    assert len(data["recommendations"]) >= 1
    assert any("unused" in r for r in data["recommendations"])
    assert any("cost" in r for r in data["recommendations"])


@pytest.mark.asyncio
async def test_context_health_check_api(client: AsyncClient, db_session: AsyncSession) -> None:
    """Verify context health-check API triggers a job and stores scores."""
    # 1. Setup workspace & Context
    ws_res = await client.post("/api/v1/workspaces", json={"name": "Health Space"})
    ws_id = ws_res.json()["id"]

    ctx = Context(
        workspace_id=ws_id,
        title="Stale Document",
        slug="stale-document",
        content="This is content that is old.",
        context_type="knowledge",
        confidence=0.8,
    )
    db_session.add(ctx)
    await db_session.commit()

    # 2. Call health-check trigger API
    res = await client.post(f"/api/v1/workspaces/{ws_id}/contexts/health-check")
    assert res.status_code == 202
    job_id = res.json()["job_id"]
    assert res.json()["status"] == "pending"

    # 3. Execute runner synchronously
    await run_context_health_check(job_id, ws_id)

    # 4. Fetch health scores
    res_scores = await client.get(f"/api/v1/workspaces/{ws_id}/contexts/health-scores")
    assert res_scores.status_code == 200
    scores = res_scores.json()
    assert len(scores) == 1
    assert scores[0]["context_id"] == ctx.id
    assert scores[0]["overall_health"] > 0.0
    assert scores[0]["quality_score"] == 0.8
    assert "evaluated_at" in scores[0]


@pytest.mark.asyncio
async def test_journal_crud_api(client: AsyncClient) -> None:
    """Verify CRUD endpoints for conversation journals."""
    # 1. Setup workspace
    ws_res = await client.post("/api/v1/workspaces", json={"name": "Journal Space"})
    ws_id = ws_res.json()["id"]

    # 2. Create Journal
    payload = {
        "workspace_id": ws_id,
        "title": "My Reflection Today",
        "content": "Today I designed background task executors. They run very smoothly.",
        "mood": "creative",
        "tags": ["design", "async"]
    }
    res = await client.post("/api/v1/journals", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "My Reflection Today"
    assert data["mood"] == "creative"
    assert "async" in data["tags"]
    journal_id = data["id"]

    # 3. List journals (with workspace filter)
    res_list = await client.get(f"/api/v1/journals?workspace_id={ws_id}")
    assert res_list.status_code == 200
    journals = res_list.json()
    assert len(journals) == 1
    assert journals[0]["id"] == journal_id

    # 4. Search journals
    res_search = await client.get(f"/api/v1/journals?q=executors")
    assert res_search.status_code == 200
    search_results = res_search.json()
    assert len(search_results) == 1
    assert search_results[0]["id"] == journal_id

    # 5. Update journal (Pin and edit content)
    res_update = await client.put(f"/api/v1/journals/{journal_id}", json={"is_pinned": 1, "content": "Updated content"})
    assert res_update.status_code == 200
    assert res_update.json()["is_pinned"] == 1
    assert res_update.json()["content"] == "Updated content"

    # 6. Delete journal
    res_del = await client.delete(f"/api/v1/journals/{journal_id}")
    assert res_del.status_code == 204

    # 7. Verify soft-deleted
    res_get = await client.get(f"/api/v1/journals/{journal_id}")
    assert res_get.status_code == 404


@pytest.mark.asyncio
async def test_workspace_export_import_json(client: AsyncClient, db_session: AsyncSession) -> None:
    """Verify workspace export to JSON and import into another workspace (Round-trip verification)."""
    from app.models import Template

    # 1. Setup original workspace, context and template
    ws_res1 = await client.post("/api/v1/workspaces", json={"name": "Source Space"})
    ws_id1 = ws_res1.json()["id"]

    c_payload = {
        "title": "Core Context",
        "content": "Original Content",
        "context_type": "knowledge",
        "priority": 75,
    }
    await client.post(f"/api/v1/workspaces/{ws_id1}/contexts", json=c_payload)

    tmpl = Template(
        workspace_id=ws_id1,
        title="Welcome Template",
        slug="welcome-template",
        content="Welcome to pocket!",
        description="A template to say welcome",
    )
    db_session.add(tmpl)
    await db_session.commit()

    # 2. Export original workspace
    export_res = await client.get(f"/api/v1/workspaces/{ws_id1}/export")
    assert export_res.status_code == 200
    export_data = export_res.json()
    assert export_data["workspace_name"] == "Source Space"
    assert len(export_data["contexts"]) == 1
    assert export_data["contexts"][0]["title"] == "Core Context"
    assert len(export_data["templates"]) == 1
    assert export_data["templates"][0]["title"] == "Welcome Template"

    # 3. Create destination workspace and Import
    ws_res2 = await client.post("/api/v1/workspaces", json={"name": "Destination Space"})
    ws_id2 = ws_res2.json()["id"]

    import_res = await client.post(f"/api/v1/workspaces/{ws_id2}/import", json=export_data)
    assert import_res.status_code == 200
    assert import_res.json()["contexts_imported"] == 1
    assert import_res.json()["templates_imported"] == 1

    # 4. Verify imported Context and Template in database
    stmt_ctx = select(Context).where(Context.workspace_id == ws_id2)
    contexts = (await db_session.execute(stmt_ctx)).scalars().all()
    assert len(contexts) == 1
    assert contexts[0].title == "Core Context"
    assert contexts[0].content == "Original Content"

    stmt_tmpl = select(Template).where(Template.workspace_id == ws_id2)
    templates = (await db_session.execute(stmt_tmpl)).scalars().all()
    assert len(templates) == 1
    assert templates[0].title == "Welcome Template"


@pytest.mark.asyncio
async def test_workspace_import_markdown_api(client: AsyncClient, db_session: AsyncSession) -> None:
    """Verify importing context from uploaded markdown file with yaml frontmatter."""
    # 1. Setup workspace
    ws_res = await client.post("/api/v1/workspaces", json={"name": "MD Space"})
    ws_id = ws_res.json()["id"]

    # 2. Mock markdown file with frontmatter
    markdown_content = (
        "---\n"
        "title: Quantum Field Theory\n"
        "context_type: persona\n"
        "tags: [quantum, physics, science]\n"
        "priority: 95\n"
        "---\n"
        "This is the body of the quantum field theory context.\n"
    )

    # 3. Call Upload API
    res = await client.post(
        f"/api/v1/workspaces/{ws_id}/import/markdown",
        files={"file": ("quantum_doc.md", markdown_content, "text/markdown")}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    context_id = res.json()["context_id"]

    # 4. Verify Context and Tags created in database
    stmt = select(Context).options(selectinload(Context.tags)).where(Context.id == context_id)
    ctx = (await db_session.execute(stmt)).scalar()
    assert ctx is not None
    assert ctx.title == "Quantum Field Theory"
    assert ctx.content == "This is the body of the quantum field theory context."
    assert ctx.context_type == "persona"
    
    tags = [t.name for t in ctx.tags]
    assert "quantum" in tags
    assert "physics" in tags
    assert "science" in tags




