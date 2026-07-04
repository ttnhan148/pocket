"""Token management and counting utilities using tiktoken."""

from __future__ import annotations

import logging
from typing import Dict, List

import tiktoken

from app.config import Settings

logger = logging.getLogger("pocket.ai.pipeline.token_counter")


class TokenCounter:
    """Manages token counting and budget allocations for prompt assembly."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        try:
            # cl100k_base is used by gpt-4, gpt-3.5-turbo, text-embedding-3-large etc.
            self._encoding = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning("Failed to initialize tiktoken, falling back to approximation: %s", str(e))
            self._encoding = None

    def count(self, text: str) -> int:
        """Counts the tokens in a single string of text."""
        if not text:
            return 0
        if self._encoding:
            try:
                return len(self._encoding.encode(text))
            except Exception:
                pass
        # Fallback to standard token estimation (approx 4 chars per token)
        return max(1, len(text) // 4)

    def count_messages(self, messages: List[Dict[str, str]]) -> int:
        """Counts tokens for a list of messages (mimics OpenAI message format parsing)."""
        if not messages:
            return 0
        
        num_tokens = 0
        for message in messages:
            # every message follows <im_start>{role/name}\n{content}<im_end>\n
            num_tokens += 4
            for key, value in message.items():
                num_tokens += self.count(value)
                if key == "name":
                    num_tokens += 1  # if there's a name, the role is omitted
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens

    def truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncates text to fit within a maximum token count."""
        if not text or max_tokens <= 0:
            return ""

        if self.count(text) <= max_tokens:
            return text

        if self._encoding:
            try:
                tokens = self._encoding.encode(text)
                truncated_tokens = tokens[:max_tokens]
                return self._encoding.decode(truncated_tokens)
            except Exception:
                pass

        # Heuristic fallback: characters approx 4 * max_tokens
        char_limit = max_tokens * 4
        return text[:char_limit]
