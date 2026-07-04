"""Intent classification pipeline step."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.ai.client import AzureAIClient
from app.ai.pipeline.base import IntentResult, PipelineContext, PipelineStep
from app.config import Settings

logger = logging.getLogger("pocket.ai.pipeline.intent")

INTENT_DETECTION_PROMPT = """You are an intent classifier. Analyze the user's message and return JSON:
{
  "intent": "question|instruction|creative|analysis|code|conversation",
  "entities": ["entity1", "entity2"],
  "complexity": "simple|moderate|complex",
  "language": "en|vi|...",
  "suggested_model": "gpt-4.1|gpt-4.1-mini"
}

Rules:
- "question" = user asking for information
- "instruction" = user giving a task to execute
- "creative" = writing, brainstorming, ideation
- "analysis" = code review, data analysis, evaluation
- "code" = code generation, debugging, refactoring
- "conversation" = casual chat, follow-up
- Use "gpt-4.1-mini" for simple questions and casual conversation
- Use "gpt-4.1" for everything else
"""


class IntentDetector(PipelineStep):
    """Classifies user intent, extracts entities, and routes to appropriate LLM."""
    name = "intent_detection"

    def __init__(self, ai_client: AzureAIClient, settings: Settings) -> None:
        self._ai_client = ai_client
        self._settings = settings

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        if not self._settings.azure_openai_endpoint:
            return self.fallback(ctx)

        try:
            result = await self._ai_client.chat_json(
                messages=[
                    {"role": "system", "content": INTENT_DETECTION_PROMPT},
                    {"role": "user", "content": ctx.input.user_message},
                ],
                model=self._settings.azure_openai_deployment_chat_mini,
                temperature=0.1,
                max_tokens=500,
            )
            
            # Map values defensively
            intent = result.get("intent", "instruction")
            entities = result.get("entities", [])
            complexity = result.get("complexity", "moderate")
            language = result.get("language", "en")
            suggested_model = result.get("suggested_model", "gpt-4.1")

            # Validate suggested model to match the deployment names
            if "mini" in suggested_model.lower():
                model_name = self._settings.azure_openai_deployment_chat_mini
            else:
                model_name = self._settings.azure_openai_deployment_chat

            ctx.intent = IntentResult(
                intent=intent,
                entities=entities,
                complexity=complexity,
                language=language,
                suggested_model=model_name,
            )
            ctx.selected_model = model_name
        except Exception as e:
            logger.warning("Intent classification failed, falling back: %s", str(e))
            return self.fallback(ctx)

        return ctx

    def fallback(self, ctx: PipelineContext) -> PipelineContext:
        model_name = self._settings.azure_openai_deployment_chat
        ctx.intent = IntentResult(
            intent="instruction",
            entities=[],
            complexity="moderate",
            language="en",
            suggested_model=model_name,
        )
        ctx.selected_model = model_name
        return ctx

    def summarize_input(self, ctx: PipelineContext) -> str:
        return f"Message: {ctx.input.user_message[:50]}..."

    def summarize_output(self, ctx: PipelineContext) -> str:
        if ctx.intent:
            return f"Intent: {ctx.intent.intent}, Model: {ctx.intent.suggested_model}"
        return "No intent detected"
