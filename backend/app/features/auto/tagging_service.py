"""AI-powered auto tagging and variable extraction service."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from app.config import Settings
from app.ai.client import AzureAIClient

logger = logging.getLogger("pocket.features.auto.tagging")

TAG_SUGGESTION_PROMPT = """You are a taxonomy expert. Suggest 3 to 5 relevant tags (short, lowercase, single-word or hyphenated-word keywords) for the following content.
Return JSON format strictly:
{
  "tags": ["tag1", "tag2", "tag3"]
}
"""

VARIABLE_EXTRACTION_PROMPT = """You are a template parameterizer. Analyze the following text and extract potential variables or hardcoded values that could be parameterized.
For each variable, suggest a parameter name, a default value based on the text, and a confidence score between 0.0 and 1.0.
Return JSON format strictly:
{
  "variables": [
    {"name": "variable_name", "suggested_value": "default_value", "confidence": 0.9}
  ]
}
"""


class AutoTaggingService:
    """Provides AI suggestions for tagging contexts and parameterizing templates."""

    def __init__(self, ai_client: AzureAIClient, settings: Settings) -> None:
        self._ai_client = ai_client
        self._settings = settings

    async def suggest_tags(self, content: str) -> List[str]:
        """Call AI to suggest tags based on context content."""
        if not self._settings.azure_openai_endpoint:
            return ["general"]

        try:
            result = await self._ai_client.chat_json(
                messages=[
                    {"role": "system", "content": TAG_SUGGESTION_PROMPT},
                    {"role": "user", "content": content},
                ],
                model=self._settings.azure_openai_deployment_chat_mini,
                temperature=0.2,
            )
            return result.get("tags", [])
        except Exception as e:
            logger.warning("AI tag suggestion failed: %s", str(e))
            return ["general"]

    async def extract_variables(self, content: str) -> List[Dict[str, Any]]:
        """Call AI to extract potential parameters from prompt template content."""
        if not self._settings.azure_openai_endpoint:
            return []

        try:
            result = await self._ai_client.chat_json(
                messages=[
                    {"role": "system", "content": VARIABLE_EXTRACTION_PROMPT},
                    {"role": "user", "content": content},
                ],
                model=self._settings.azure_openai_deployment_chat_mini,
                temperature=0.2,
            )
            return result.get("variables", [])
        except Exception as e:
            logger.warning("AI variable extraction failed: %s", str(e))
            return []
