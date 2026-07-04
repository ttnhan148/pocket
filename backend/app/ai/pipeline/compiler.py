"""Prompt compiler step."""

from __future__ import annotations

import logging
from typing import Any, List

import jinja2

from app.ai.pipeline.base import PipelineContext, PipelineStep

logger = logging.getLogger("pocket.ai.pipeline.compiler")


class PromptCompiler(PipelineStep):
    """Compiles the final system prompt from contexts, variables, and templates."""
    name = "prompt_compilation"

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        # 1. Determine which contexts to compile.
        # Use ranked_contexts if available, otherwise retrieved_contexts.
        contexts = []
        if ctx.ranked_contexts:
            # ranked_contexts are RankedContext objects wrapping the DB Context model
            contexts = [rc.context for rc in ctx.ranked_contexts]
        else:
            contexts = ctx.retrieved_contexts

        # 2. Build system prompt sections grouped by type in the defined order
        type_order = [
            "persona",
            "role",
            "instruction",
            "knowledge",
            "constraint",
            "example",
            "reference",
            "snippet",
        ]

        sections: List[str] = []
        for ctx_type in type_order:
            type_contexts = [c for c in contexts if c.context_type == ctx_type]
            if type_contexts:
                section_header = f"## {ctx_type.upper()}"
                section_content = "\n\n".join(c.content for c in type_contexts)
                sections.append(f"{section_header}\n\n{section_content}")

        system_prompt = "\n\n---\n\n".join(sections)

        # 3. Resolve Jinja2 variables in system prompt
        resolved_vars = ctx.resolved_variables.variables if ctx.resolved_variables else {}
        if resolved_vars:
            try:
                template = jinja2.Template(system_prompt)
                system_prompt = template.render(**resolved_vars)
            except Exception as e:
                logger.warning("Jinja2 rendering of system prompt sections failed: %s", str(e))

        # 4. If a prompt template is specified, render the template wrapping the contexts
        # (Usually templates have placeholders for variables and also contexts)
        # Note: If no template is specified, compiled system_prompt is the system prompt itself.
        ctx.system_prompt = system_prompt
        ctx.final_prompt = system_prompt

        # 5. Build compiled messages list (System prompt + History + User message)
        messages = [{"role": "system", "content": system_prompt}]

        # Include history if available
        if ctx.conversation_history:
            messages.extend(ctx.conversation_history)

        # Append new user message
        messages.append({"role": "user", "content": ctx.input.user_message})

        ctx.compiled_messages = messages
        return ctx

    def summarize_input(self, ctx: PipelineContext) -> str:
        ctxs_count = len(ctx.ranked_contexts or ctx.retrieved_contexts)
        return f"Contexts: {ctxs_count}, History messages: {len(ctx.conversation_history)}"

    def summarize_output(self, ctx: PipelineContext) -> str:
        return f"System Prompt Length: {len(ctx.system_prompt)} chars, Total Messages: {len(ctx.compiled_messages)}"
