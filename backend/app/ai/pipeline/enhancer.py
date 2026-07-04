"""AI-powered prompt enhancement step."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.ai.client import AzureAIClient
from app.ai.pipeline.base import PipelineContext, PipelineStep
from app.config import Settings

logger = logging.getLogger("pocket.ai.pipeline.enhancer")

ENHANCE_PROMPT = """You are a prompt engineering expert. Your job is to improve the user's compiled prompt.
Rewrite the compiled prompt to be extremely clear, specific, structured, and effective for LLMs.
Return JSON format:
{
  "enhanced_prompt": "...",
  "changes": ["list of improvements made"]
}
"""


class PromptEnhancer(PipelineStep):
    """Uses AI to improve prompt clarity and specificity."""
    name = "ai_enhancement"

    def __init__(self, ai_client: AzureAIClient, settings: Settings) -> None:
        self._ai_client = ai_client
        self._settings = settings

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        if not self._settings.azure_openai_endpoint or not getattr(self._settings, "ai_enhancement_enabled", True):
            return ctx

        try:
            result = await self._ai_client.chat_json(
                messages=[
                    {"role": "system", "content": ENHANCE_PROMPT},
                    {"role": "user", "content": json.dumps({
                        "original_prompt": ctx.final_prompt,
                        "user_intent": ctx.input.user_message,
                        "intent_analysis": {
                            "intent": ctx.intent.intent,
                            "entities": ctx.intent.entities,
                            "complexity": ctx.intent.complexity,
                        } if ctx.intent else None,
                    })},
                ],
                model=self._settings.azure_openai_deployment_chat,
                temperature=0.4,
            )
            
            enhanced = result.get("enhanced_prompt")
            if enhanced:
                ctx.final_prompt = enhanced
                ctx.enhancement_notes = result.get("changes", [])
                
                # Sync final compiled prompt to compiled messages
                if ctx.compiled_messages and ctx.compiled_messages[0]["role"] == "system":
                    ctx.compiled_messages[0]["content"] = enhanced
        except Exception as e:
            logger.warning("Prompt enhancement step failed: %s", str(e))

        return ctx
