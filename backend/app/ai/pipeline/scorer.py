"""AI-evaluated prompt quality scoring step."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.ai.client import AzureAIClient
from app.ai.pipeline.base import PipelineContext, PipelineStep, PromptScore
from app.config import Settings

logger = logging.getLogger("pocket.ai.pipeline.scorer")

SCORING_PROMPT = """You are a prompt quality evaluator. Score the following prompt on these dimensions (0.0 to 1.0):

1. **Clarity** (0-1): Is the prompt clear and unambiguous? Are instructions easy to follow?
2. **Specificity** (0-1): Does it provide enough detail for the AI to produce the desired output?
3. **Completeness** (0-1): Does it include role, task, constraints, output format, and examples?
4. **Consistency** (0-1): Are there any contradictions or conflicting instructions?
5. **Efficiency** (0-1): Is the prompt concise? No unnecessary repetition or verbosity?

Return JSON format strictly:
{
  "overall": 0.85,
  "clarity": 0.9,
  "specificity": 0.8,
  "completeness": 0.85,
  "consistency": 0.95,
  "efficiency": 0.75,
  "reasoning": "The prompt is well-structured with clear role definition...",
  "suggestions": ["Add output format specification", "Remove redundant constraint"]
}
"""


class PromptScorer(PipelineStep):
    """Evaluates and scores a prompt across 5 dimensions using AI."""
    name = "prompt_scoring"

    def __init__(self, ai_client: AzureAIClient, settings: Settings) -> None:
        self._ai_client = ai_client
        self._settings = settings

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        if not self._settings.azure_openai_endpoint or not getattr(self._settings, "ai_scoring_enabled", True):
            # Fallback local mock score
            ctx.prompt_score = self.fallback_score(ctx)
            return ctx

        try:
            result = await self._ai_client.chat_json(
                messages=[
                    {"role": "system", "content": SCORING_PROMPT},
                    {"role": "user", "content": ctx.final_prompt},
                ],
                model=self._settings.azure_openai_deployment_chat_mini,
                temperature=0.1,
            )

            ctx.prompt_score = PromptScore(
                overall=float(result.get("overall", 0.5)),
                clarity=float(result.get("clarity", 0.5)),
                specificity=float(result.get("specificity", 0.5)),
                completeness=float(result.get("completeness", 0.5)),
                consistency=float(result.get("consistency", 0.5)),
                efficiency=float(result.get("efficiency", 0.5)),
                reasoning=result.get("reasoning", "Evaluation complete."),
                suggestions=result.get("suggestions", []),
            )
        except Exception as e:
            logger.warning("Prompt scoring step failed: %s", str(e))
            ctx.prompt_score = self.fallback_score(ctx)

        return ctx

    def fallback_score(self, ctx: PipelineContext) -> PromptScore:
        # Simple heuristic scoring if offline
        length = len(ctx.final_prompt)
        base_score = min(0.9, length / 1000.0) if length > 0 else 0.0
        return PromptScore(
            overall=base_score,
            clarity=base_score,
            specificity=base_score,
            completeness=base_score,
            consistency=0.9,
            efficiency=0.8,
            reasoning="Fallback offline heuristic score.",
            suggestions=["Connect to Azure OpenAI to get full AI-powered prompt analysis."]
        )
