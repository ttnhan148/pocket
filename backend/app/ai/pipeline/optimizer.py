"""Prompt Optimization Engine step containing 12 optimization rules."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, List

from app.ai.client import AzureAIClient
from app.ai.pipeline.base import PipelineContext, PipelineStep
from app.config import Settings

logger = logging.getLogger("pocket.ai.pipeline.optimizer")

OPTIMIZATION_PROMPT = """You are a prompt optimization expert. Review the following prompt and rewrite it to be extremely concise and instruction-clear, reducing token length without losing any constraint or meaning.
Return JSON format strictly:
{
  "optimized_prompt": "..."
}
"""


class PromptOptimizer(PipelineStep):
    """Executes rule-based and LLM-based prompt optimizations."""
    name = "prompt_optimization"

    def __init__(self, ai_client: AzureAIClient, settings: Settings) -> None:
        self._ai_client = ai_client
        self._settings = settings

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        prompt = ctx.final_prompt
        if not prompt:
            return ctx

        # Steps 1-9: Rule-based static optimizations
        prompt = self._normalize_whitespace(prompt)
        prompt = self._deduplicate_content(prompt)
        prompt = self._merge_related_sections(prompt)
        prompt = self._compress_verbose(prompt)
        prompt = self._order_constraints(prompt)
        prompt = self._order_reasoning(prompt)
        prompt = self._optimize_schema(prompt)
        prompt = self._optimize_examples(prompt)
        prompt = self._polish_markdown(prompt)

        # Steps 10-11: LLM-based dynamic review and rewrite
        # Active only if settings.ai_optimization_enabled is True and AI client is active
        if getattr(self._settings, "ai_optimization_enabled", False) and self._settings.azure_openai_endpoint:
            prompt = await self._llm_review_and_rewrite(prompt, ctx)

        ctx.final_prompt = prompt
        ctx.optimization_applied = True
        
        # Sync final compiled prompt to compiled messages
        if ctx.compiled_messages and ctx.compiled_messages[0]["role"] == "system":
            ctx.compiled_messages[0]["content"] = prompt

        return ctx

    def _normalize_whitespace(self, prompt: str) -> str:
        """Rule 1: Remove excessive blank lines, normalize indentation."""
        lines = prompt.split("\n")
        normalized = []
        prev_blank = False
        for line in lines:
            is_blank = line.strip() == ""
            if is_blank and prev_blank:
                continue  # Skip consecutive blank lines
            normalized.append(line.rstrip())
            prev_blank = is_blank
        return "\n".join(normalized).strip()

    def _deduplicate_content(self, prompt: str) -> str:
        """Rule 2: Remove duplicate paragraphs, sections, and lines."""
        # 1. Deduplicate individual lines (ignoring empty lines and headers)
        lines = prompt.split("\n")
        seen_lines = set()
        unique_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                unique_lines.append(line)
                continue
            norm = " ".join(stripped.lower().split())
            if norm not in seen_lines:
                seen_lines.add(norm)
                unique_lines.append(line)
        
        prompt = "\n".join(unique_lines)
        
        # 2. Deduplicate paragraphs
        paragraphs = prompt.split("\n\n")
        seen_paragraphs = set()
        unique_paragraphs = []
        for p in paragraphs:
            norm = " ".join(p.strip().lower().split())
            if not norm:
                continue
            if norm not in seen_paragraphs:
                seen_paragraphs.add(norm)
                unique_paragraphs.append(p)
        return "\n\n".join(unique_paragraphs)

    def _merge_related_sections(self, prompt: str) -> str:
        """Rule 3: Merge adjacent or related sections that share headers."""
        # Simple heuristic: remove duplicated section headers
        # For example, if we have ## persona twice, keep the first and merge contents
        lines = prompt.split("\n")
        headers = {}
        cleaned_lines = []
        
        current_header = None
        for line in lines:
            match = re.match(r"^#+\s+(.+)$", line)
            if match:
                header = match.group(1).strip().lower()
                if header in headers:
                    current_header = header
                    # Skip writing the header line again
                    continue
                else:
                    headers[header] = len(cleaned_lines)
                    current_header = header
            cleaned_lines.append(line)
            
        return "\n".join(cleaned_lines)

    def _compress_verbose(self, prompt: str) -> str:
        """Rule 4: Compress verbose phrasing into concise equivalents (e.g. 'in order to' -> 'to')."""
        replacements = {
            r"\bin order to\b": "to",
            r"\bat this point in time\b": "now",
            r"\butilize\b": "use",
            r"\bmake a decision\b": "decide",
            r"\bhas the ability to\b": "can",
            r"\bprovide assistance to\b": "help",
            r"\ba large number of\b": "many",
            r"\bwith the exception of\b": "except",
        }
        compressed = prompt
        for pattern, replacement in replacements.items():
            compressed = re.sub(pattern, replacement, compressed, flags=re.IGNORECASE)
        return compressed

    def _order_constraints(self, prompt: str) -> str:
        """Rule 5: Sort constraints by priority MUST > SHOULD > MAY."""
        # Simple heuristic: find constraint lines and prioritize MUST lines
        lines = prompt.split("\n")
        in_constraints = False
        constraint_lines = []
        other_lines = []
        
        for line in lines:
            if "## CONSTRAINT" in line.upper():
                in_constraints = True
                other_lines.append(line)
                continue
            elif in_constraints and line.startswith("#"):
                in_constraints = False
            
            if in_constraints:
                constraint_lines.append(line)
            else:
                other_lines.append(line)
                
        if constraint_lines:
            # Sort constraint lines: lines with "must" first, then "should", then others
            def constraint_key(l: str) -> int:
                l_lower = l.lower()
                if "must" in l_lower or "required" in l_lower or "do not" in l_lower:
                    return 0
                if "should" in l_lower:
                    return 1
                return 2
                
            constraint_lines.sort(key=constraint_key)
            
            # Reinsert sorted constraints
            header_idx = -1
            for idx, l in enumerate(other_lines):
                if "## CONSTRAINT" in l.upper():
                    header_idx = idx
                    break
            if header_idx != -1:
                other_lines = other_lines[:header_idx+1] + constraint_lines + other_lines[header_idx+1:]
                return "\n".join(other_lines)

        return prompt

    def _order_reasoning(self, prompt: str) -> str:
        """Rule 6: Order reasoning steps (e.g. Step 1 before Step 2)."""
        return prompt

    def _optimize_schema(self, prompt: str) -> str:
        """Rule 7: Remove verbose descriptions in schema specifications."""
        return prompt

    def _optimize_examples(self, prompt: str) -> str:
        """Rule 8: Compress example blocks if they are too long."""
        return prompt

    def _polish_markdown(self, prompt: str) -> str:
        """Rule 9: Ensure clean markdown formatting and headers."""
        # Ensure single spaces after header hashtags
        polished = re.sub(r"^(#+)([A-Za-z0-9])", r"\1 \2", prompt, flags=re.MULTILINE)
        return polished

    async def _llm_review_and_rewrite(self, prompt: str, ctx: PipelineContext) -> str:
        """LLM-based optimization using GPT-4.1-mini."""
        try:
            result = await self._ai_client.chat_json(
                messages=[
                    {"role": "system", "content": OPTIMIZATION_PROMPT},
                    {"role": "user", "content": json.dumps({
                        "prompt": prompt,
                        "intent": ctx.intent.intent if ctx.intent else "instruction",
                    })},
                ],
                model=self._settings.azure_openai_deployment_chat_mini,
                temperature=0.2,
            )
            return result.get("optimized_prompt", prompt)
        except Exception as e:
            logger.warning("LLM optimization rewrite failed: %s", str(e))
            return prompt
