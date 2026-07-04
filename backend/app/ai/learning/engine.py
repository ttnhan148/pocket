"""AI Learning Engine for post-conversation pattern analysis and optimization."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.ai.client import AzureAIClient
from app.features.context.service import ContextService
from app.models import (
    ContextCandidate,
    Conversation,
    LearningRecord,
    Message,
    PromptRun,
)

logger = logging.getLogger("pocket.ai.learning.engine")

LEARNING_ANALYSIS_PROMPT = """Analyze this AI conversation and provide insights in JSON format:

{
  "quality_assessment": "good|fair|poor",
  "missing_contexts": [
    {
      "topic": "What context was missing",
      "impact": "How it affected the conversation"
    }
  ],
  "successes": ["success factor 1", "success factor 2"],
  "failures": ["failure factor 1", "failure factor 2"],
  "recommendations": ["recommendation 1"],
  "new_context_suggestions": [
    {
      "title": "Suggested Context Title",
      "content": "Suggested markdown content for the new context",
      "type": "knowledge|persona|instruction|constraint",
      "reasoning": "Why this context is suggested",
      "confidence": 0.85
    }
  ],
  "context_effectiveness": [
    {
      "context_id": "id_of_used_context",
      "confidence_delta": 0.05
    }
  ]
}
"""


class LearningEngine:
    """Post-conversation learning analyzer."""

    def __init__(self, db: AsyncSession, ai_client: AzureAIClient, settings: Settings) -> None:
        self.db = db
        self._ai_client = ai_client
        self._settings = settings
        self._context_service = ContextService(db)

    async def analyze_conversation(self, conversation_id: str) -> LearningRecord | None:
        """Fetch conversation, perform LLM analysis, update context scores, and store suggestions."""
        if not self._settings.azure_openai_endpoint:
            return None

        # 1. Fetch conversation and messages
        stmt_conv = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.deleted_at.is_(None)
        )
        res_conv = await self.db.execute(stmt_conv)
        conversation = res_conv.scalar_one_or_none()
        if not conversation:
            logger.warning("Conversation %s not found for learning engine.", conversation_id)
            return None

        stmt_msgs = select(Message).where(
            Message.conversation_id == conversation_id,
            Message.deleted_at.is_(None)
        ).order_by(Message.created_at.asc())
        res_msgs = await self.db.execute(stmt_msgs)
        messages = list(res_msgs.scalars().all())

        # 2. Fetch prompt runs (to see what contexts were used)
        stmt_runs = select(PromptRun).where(
            PromptRun.conversation_id == conversation_id,
            PromptRun.deleted_at.is_(None)
        )
        res_runs = await self.db.execute(stmt_runs)
        prompt_runs = list(res_runs.scalars().all())

        # 3. Call AI to analyze conversation
        try:
            analysis = await self._ai_client.chat_json(
                messages=[
                    {"role": "system", "content": LEARNING_ANALYSIS_PROMPT},
                    {"role": "user", "content": json.dumps({
                        "messages": [
                            {"role": m.role, "content": m.content[:1000]}
                            for m in messages
                        ],
                        "prompt_runs": [
                            {
                                "compiled_prompt": r.compiled_prompt[:1000],
                                "variables_used": r.variables_used
                            }
                            for r in prompt_runs
                        ]
                    })},
                ],
                model=self._settings.azure_openai_deployment_chat_mini,
                temperature=0.2,
            )

            # 4. Create LearningRecord
            record = LearningRecord(
                conversation_id=conversation_id,
                analysis=json.dumps(analysis),
                missing_contexts=json.dumps(analysis.get("missing_contexts", [])),
                success_factors=json.dumps(analysis.get("successes", [])),
                failure_factors=json.dumps(analysis.get("failures", [])),
                recommendations=json.dumps(analysis.get("recommendations", [])),
                applied=0,
            )
            self.db.add(record)
            await self.db.flush()

            # 5. Create ContextCandidates
            for candidate in analysis.get("new_context_suggestions", []):
                cc = ContextCandidate(
                    learning_record_id=record.id,
                    workspace_id=conversation.workspace_id,
                    suggested_title=candidate["title"],
                    suggested_content=candidate["content"],
                    suggested_type=candidate["type"],
                    reasoning=candidate["reasoning"],
                    confidence=float(candidate.get("confidence", 0.7)),
                    status="pending",
                )
                self.db.add(cc)

            # 6. Update Context scores
            for ctx_usage in analysis.get("context_effectiveness", []):
                try:
                    await self._context_service.update_scores(
                        context_id=ctx_usage["context_id"],
                        delta_confidence=float(ctx_usage.get("confidence_delta", 0.0)),
                        delta_usage=1,
                    )
                except Exception as e:
                    logger.warning("Could not update score for context %s: %s", ctx_usage.get("context_id"), str(e))

            await self.db.flush()
            return record

        except Exception as e:
            logger.error("Learning Engine analysis failed for conversation %s: %s", conversation_id, str(e), exc_info=True)
            return None
