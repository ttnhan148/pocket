"""Integration tests for Conversation backend and Prompt Compile endpoints (M33-M35)."""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation, Message, PromptRun, Workspace, Context
from app.ai.client import AzureAIClient, ChatResult


@pytest.mark.asyncio
async def test_conversation_api_lifecycle(client: AsyncClient, db_session: AsyncSession) -> None:
    """Verify full conversation lifecycle, message pipeline execution, and compile endpoint."""
    
    # 1. Create a Workspace
    workspace_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Chat Space", "description": "Workspace for testing chat"},
    )
    assert workspace_res.status_code == 201
    workspace_id = workspace_res.json()["id"]

    # Add a mock context to search/retrieve
    ctx = Context(
        workspace_id=workspace_id,
        title="Persona Math",
        slug="persona-math",
        content="You are a smart mathematician.",
        context_type="persona",
    )
    db_session.add(ctx)
    await db_session.commit()

    # 2. Create a Conversation
    conv_payload = {
        "workspace_id": workspace_id,
        "title": "Algebra Study",
        "model": "gpt-4.1",
        "system_prompt": "Help with homework"
    }
    create_res = await client.post("/api/v1/conversations", json=conv_payload)
    assert create_res.status_code == 201
    conversation = create_res.json()
    conversation_id = conversation["id"]
    assert conversation["title"] == "Algebra Study"
    assert conversation["message_count"] == 0

    # 3. List conversations
    list_res = await client.get(f"/api/v1/conversations?workspace_id={workspace_id}")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 4. Send Message (with mocked AI client)
    mock_chat_result = ChatResult(
        content="2 + 2 is equal to 4.",
        finish_reason="stop",
        prompt_tokens=30,
        completion_tokens=15,
        total_tokens=45,
        model="gpt-4.1",
        cost=0.0015,
    )

    with patch("app.features.conversation.service.AzureAIClient") as mock_client_cls:
        # Mock instance methods
        mock_client_instance = MagicMock(spec=AzureAIClient)
        mock_client_instance.chat = AsyncMock(return_value=mock_chat_result)
        mock_client_instance.chat_json = AsyncMock(return_value={
            "intent": "question",
            "entities": [],
            "complexity": "simple",
            "language": "en",
            "suggested_model": "gpt-4.1-mini"
        })
        mock_client_cls.return_value = mock_client_instance

        # Send User Message
        msg_payload = {"content": "Solve 2+2"}
        msg_res = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json=msg_payload
        )
        assert msg_res.status_code == 201
        res_data = msg_res.json()
        assert res_data["role"] == "assistant"
        assert "4." in res_data["content"]
        assert res_data["cost"] > 0.0

    # 5. Verify database updates
    # Conversation totals should be updated
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    conv_db = (await db_session.execute(stmt)).scalar()
    assert conv_db.message_count == 2
    assert conv_db.total_tokens == 45
    assert conv_db.total_cost > 0.0

    # Verify PromptRun was stored
    stmt_run = select(PromptRun).where(PromptRun.conversation_id == conversation_id)
    run_db = (await db_session.execute(stmt_run)).scalar()
    assert run_db is not None
    assert run_db.user_input == "Solve 2+2"
    assert run_db.model == "gpt-4.1"

    # 6. Test Compile Preview Endpoint (/api/v1/prompts/compile)
    compile_payload = {
        "workspace_id": workspace_id,
        "user_message": "Solve algebraic formula",
        "selected_context_ids": [ctx.id],
        "variable_overrides": {"topic": "algebra"}
    }
    
    with patch("app.features.prompt.router.AzureAIClient") as mock_prompt_client_cls:
        mock_client_inst = MagicMock(spec=AzureAIClient)
        mock_client_inst.chat_json = AsyncMock(return_value={
            "intent": "question",
            "entities": [],
            "complexity": "simple",
            "language": "en",
            "suggested_model": "gpt-4.1-mini"
        })
        mock_prompt_client_cls.return_value = mock_client_inst

        comp_res = await client.post("/api/v1/prompts/compile", json=compile_payload)
        assert comp_res.status_code == 200
        comp_data = comp_res.json()
        assert "PERSONA" in comp_data["system_prompt"]
        assert "You are a smart mathematician." in comp_data["final_prompt"]
        assert comp_data["validation_result"]["passed"] is True
