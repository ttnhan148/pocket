"""AI-powered prompt critique step."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.ai.client import AzureAIClient
from app.ai.pipeline.base import CritiqueResult, PipelineContext, PipelineStep
from app.config import Settings

logger = logging.getLogger("pocket.ai.pipeline.critic")

CRITIQUE_PROMPT = """You are a critical prompt evaluator. Analyze the given prompt and provide constructive feedback.
Identify issues, suggests concrete fixes, and provide an improved version of the prompt if needed.
Return JSON format strictly:
{
  "issues": [
    {"severity": "error|warning|info", "description": "...", "fix": "..."}
  ],
  "suggestions": ["suggestion 1", "suggestion 2"],
  "assessment": "Overall assessment statement",
  "improved_prompt": "..."
}
"""


class PromptCritic(PipelineStep):
    """Uses AI to critique a prompt and identify potential issues or improvements."""
    name = "ai_critique"

    def __init__(self, ai_client: AzureAIClient, settings: Settings) -> None:
        self._ai_client = ai_client
        self._settings = settings

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        if not self._settings.azure_openai_endpoint or not getattr(self._settings, "ai_critique_enabled", True):
            return ctx

        try:
            result = await self._ai_client.chat_json(
                messages=[
                    {"role": "system", "content": CRITIQUE_PROMPT},
                    {"role": "user", "content": ctx.final_prompt},
                ],
                model=self._settings.azure_openai_deployment_chat,
                temperature=0.3,
            )
            
            ctx.critique = CritiqueResult(
                issues=result.get("issues", []),
                suggestions=result.get("suggestions", []),
                overall_assessment=result.get("assessment", ""),
            )
            
            # Apply auto-improved prompt if provided and enabled
            improved = result.get("improved_prompt")
            if improved and getattr(self._settings, "ai_critique_autofix_enabled", False):
                ctx.final_prompt = improved
                if ctx.compiled_messages and ctx.compiled_messages[0]["role"] == "system":
                    ctx.compiled_messages[0]["content"] = improved
        except Exception as e:
            logger.warning("Prompt critique step failed: %s", str(e))
            ctx.critique = CritiqueResult(overall_assessment="Critique unavailable.")

        return ctx
