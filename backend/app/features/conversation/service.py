"""Conversation and Message Service layer."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.service import BaseService
from app.config import Settings
from app.ai.client import AzureAIClient
from app.ai.embeddings import EmbeddingService
from app.ai.pipeline.retrieval import RetrievalEngine
from app.ai.pipeline.ranking import RankingEngine
from app.ai.pipeline.token_counter import TokenCounter
from app.ai.pipeline import (
    PipelineInput,
    PipelineOrchestrator,
    TokenUsage,
)
from app.features.conversation.schemas import ConversationCreate, ConversationUpdate
from app.models import (
    Conversation,
    Message,
    PromptContext,
    PromptRun,
    PromptScore,
    PromptVersion,
)

logger = logging.getLogger("pocket.features.conversation.service")


class ConversationService(BaseService):
    """Business logic service for managing chat conversations and messages."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self._settings = Settings()
        self._ai_client = AzureAIClient(self._settings)
        self._token_counter = TokenCounter(self._settings)
        self._embedding_service = EmbeddingService(self._ai_client, self._settings)
        self._retrieval_engine = RetrievalEngine(
            self._ai_client, self._embedding_service, self._settings
        )
        self._ranking_engine = RankingEngine()
        self._orchestrator = PipelineOrchestrator(
            db=self.db,
            settings=self._settings,
            ai_client=self._ai_client,
            token_counter=self._token_counter,
            retrieval_engine=self._retrieval_engine,
            ranking_engine=self._ranking_engine,
        )

    async def create_conversation(self, data: ConversationCreate) -> Conversation:
        """Create a new chat conversation."""
        conversation = Conversation(
            workspace_id=data.workspace_id,
            provider_id=data.provider_id,
            title=data.title,
            model=data.model,
            system_prompt=data.system_prompt,
            total_tokens=0,
            total_cost=0.0,
            message_count=0,
            is_pinned=0,
            is_archived=0,
        )
        self.db.add(conversation)
        await self.db.flush()
        return conversation

    async def get_conversation(self, id_: str) -> Conversation:
        """Retrieve conversation by ID or raise NotFoundError."""
        stmt = select(Conversation).where(
            Conversation.id == id_,
            Conversation.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        conversation = res.scalar_one_or_none()
        if not conversation:
            raise NotFoundError("Conversation", id_)
        return conversation

    async def list_conversations(self, workspace_id: str) -> list[Conversation]:
        """List active conversations in a workspace."""
        stmt = (
            select(Conversation)
            .where(
                Conversation.workspace_id == workspace_id,
                Conversation.deleted_at.is_(None),
            )
            .order_by(Conversation.is_pinned.desc(), Conversation.updated_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def update_conversation(self, id_: str, data: ConversationUpdate) -> Conversation:
        """Update conversation properties (title, pin, archive)."""
        conversation = await self.get_conversation(id_)
        if data.title is not None:
            conversation.title = data.title
        if data.is_pinned is not None:
            conversation.is_pinned = data.is_pinned
        if data.is_archived is not None:
            conversation.is_archived = data.is_archived
        
        conversation.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return conversation

    async def delete_conversation(self, id_: str) -> bool:
        """Soft delete conversation by ID."""
        conversation = await self.get_conversation(id_)
        conversation.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def get_messages(self, conversation_id: str) -> list[Message]:
        """Retrieve all active messages of a conversation."""
        stmt = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.deleted_at.is_(None),
            )
            .order_by(Message.created_at.asc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def send_message(self, conversation_id: str, content: str) -> Message:
        """Send message, execute Prompt Pipeline, store response, update cost/tokens."""
        conversation = await self.get_conversation(conversation_id)

        # 1. Save User Message
        user_tokens = self._token_counter.count(content)
        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=content,
            token_count=user_tokens,
            model=conversation.model,
            cost=0.0,
        )
        self.db.add(user_msg)
        await self.db.flush()

        # 2. Retrieve history for prompt pipeline context
        history_msgs = await self.get_messages(conversation_id)
        # Build history matching OpenAI message schema, excluding the last user message we just created
        history_history = []
        for m in history_msgs[:-1]:
            history_history.append({"role": m.role, "content": m.content})

        # 3. Execute Pipeline Orchestrator
        input_payload = PipelineInput(
            user_message=content,
            workspace_id=conversation.workspace_id,
            conversation_id=conversation_id,
        )
        
        # Inject existing history into pipeline
        # (Orchestrator uses ctx.conversation_history inside compiler step)
        output = await self._orchestrator.execute(input_payload)

        # 4. Save Assistant Message
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=output.ai_response,
            token_count=output.token_usage.completion if output.token_usage else 0,
            model=conversation.model,
            latency_ms=output.latency_ms,
            cost=output.cost,
            finish_reason="stop" if output.ai_response else "failed",
        )
        self.db.add(assistant_msg)
        await self.db.flush()

        # 5. Save PromptRun logs
        passed_val = 1 if (not output.validation_result or output.validation_result.passed) else 0
        validation_errs_json = None
        if output.validation_result and output.validation_result.errors:
            validation_errs_json = json.dumps([
                {"name": e.name, "message": e.message, "severity": e.severity}
                for e in output.validation_result.errors
            ])

        prompt_run = PromptRun(
            workspace_id=conversation.workspace_id,
            conversation_id=conversation_id,
            user_input=content,
            compiled_prompt=output.final_prompt,
            system_prompt=output.system_prompt,
            model=conversation.model,
            total_tokens=output.token_usage.total if output.token_usage else 0,
            prompt_tokens=output.token_usage.prompt if output.token_usage else 0,
            completion_tokens=output.token_usage.completion if output.token_usage else 0,
            cost=output.cost,
            latency_ms=output.latency_ms,
            validation_passed=passed_val,
            validation_errors=validation_errs_json,
            optimization_applied=1 if output.final_prompt != output.system_prompt else 0,
            variables_used=json.dumps(output.variables_resolved),
        )
        self.db.add(prompt_run)
        await self.db.flush()

        # 6. Save PromptContext records
        for idx, cu in enumerate(output.contexts_used):
            prompt_ctx = PromptContext(
                prompt_run_id=prompt_run.id,
                context_id=cu.id,
                rank_position=idx,
                relevance_score=cu.score,
                was_auto_included=1,
            )
            self.db.add(prompt_ctx)

        # 7. Save PromptScore if available
        if output.prompt_score:
            score_data = output.prompt_score
            prompt_score = PromptScore(
                prompt_run_id=prompt_run.id,
                overall_score=score_data.overall,
                clarity_score=score_data.clarity,
                specificity_score=score_data.specificity,
                completeness_score=score_data.completeness,
                consistency_score=score_data.consistency,
                efficiency_score=score_data.efficiency,
                reasoning=score_data.reasoning,
                suggestions=json.dumps(score_data.suggestions),
                model=conversation.model,
            )
            self.db.add(prompt_score)

        # 8. Accumulate Conversation statistics
        tokens_added = output.token_usage.total if output.token_usage else (user_tokens)
        conversation.total_tokens += tokens_added
        conversation.total_cost += output.cost
        conversation.message_count += 2
        conversation.updated_at = datetime.now(timezone.utc)
        
        await self.db.flush()
        return assistant_msg
