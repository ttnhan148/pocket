"""APIs for Conversations and Messages."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.conversation.schemas import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
)
from app.features.conversation.service import ConversationService

logger = logging.getLogger("pocket.features.conversation.router")

router = APIRouter()


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=201,
    summary="Create a new conversation",
)
async def create_conversation(
    data: ConversationCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ConversationResponse:
    """Start a new chat conversation in a workspace."""
    service = ConversationService(db)
    conversation = await service.create_conversation(data)
    return ConversationResponse.model_validate(conversation)


@router.get(
    "/{id}",
    response_model=ConversationResponse,
    summary="Get conversation details",
)
async def get_conversation(
    id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ConversationResponse:
    """Retrieve details of a single conversation by ID."""
    service = ConversationService(db)
    conversation = await service.get_conversation(id)
    return ConversationResponse.model_validate(conversation)


@router.get(
    "",
    response_model=list[ConversationResponse],
    summary="List conversations in a workspace",
)
async def list_conversations(
    workspace_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[ConversationResponse]:
    """Retrieve all conversations for a specific workspace, ordered by pin status and recency."""
    service = ConversationService(db)
    conversations = await service.list_conversations(workspace_id)
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.put(
    "/{id}",
    response_model=ConversationResponse,
    summary="Update conversation properties",
)
async def update_conversation(
    id: str,
    data: ConversationUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ConversationResponse:
    """Update title, pinned status, or archive status of a conversation."""
    service = ConversationService(db)
    conversation = await service.update_conversation(id, data)
    return ConversationResponse.model_validate(conversation)


@router.delete(
    "/{id}",
    status_code=204,
    summary="Soft delete a conversation",
)
async def delete_conversation(
    id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Soft delete conversation by ID."""
    service = ConversationService(db)
    await service.delete_conversation(id)


@router.get(
    "/{id}/messages",
    response_model=list[MessageResponse],
    summary="Get conversation messages",
)
async def get_messages(
    id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[MessageResponse]:
    """Retrieve message history of a conversation in chronological order."""
    service = ConversationService(db)
    messages = await service.get_messages(id)
    return [MessageResponse.model_validate(m) for m in messages]


@router.post(
    "/{id}/messages",
    response_model=MessageResponse,
    status_code=201,
    summary="Send a message to a conversation",
)
async def send_message(
    id: str,
    data: MessageCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> MessageResponse:
    """Send a user message, run the full AI prompt compiler pipeline, and return the AI response."""
    service = ConversationService(db)
    message = await service.send_message(conversation_id=id, content=data.content)
    return MessageResponse.model_validate(message)


@router.post(
    "/{id}/learn",
    status_code=200,
    summary="Trigger Learning Engine for a conversation",
)
async def learn_conversation(
    id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Analyze conversation patterns and generate learning records."""
    from app.config import Settings
    from app.ai.client import AzureAIClient
    from app.ai.learning.engine import LearningEngine
    
    settings = Settings()
    ai_client = AzureAIClient(settings)
    engine = LearningEngine(db, ai_client, settings)
    
    record = await engine.analyze_conversation(id)
    if record:
        return {"status": "success", "learning_record_id": record.id}
    return {"status": "skipped", "message": "Azure OpenAI not configured or conversation not found"}

