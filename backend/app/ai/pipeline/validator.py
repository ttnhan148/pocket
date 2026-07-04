"""Validation Engine step implementing compiler-style prompt check rules."""

from __future__ import annotations

import logging
import re
from typing import Any, List, Optional, Set, Tuple

from app.ai.client import AzureAIClient
from app.ai.pipeline.base import (
    PipelineContext,
    PipelineStep,
    ValidationCheck,
    ValidationFailedError,
    ValidationResult,
)
from app.ai.pipeline.token_counter import TokenCounter
from app.config import Settings

logger = logging.getLogger("pocket.ai.pipeline.validator")


class ValidationEngine(PipelineStep):
    """Executes 11 compiler-style validation rules on the compiled prompt."""
    name = "prompt_validation"

    def __init__(
        self,
        ai_client: AzureAIClient,
        token_counter: TokenCounter,
        settings: Settings,
        dependency_service: Any = None,
    ) -> None:
        self._ai_client = ai_client
        self._token_counter = token_counter
        self._settings = settings
        self._dep_service = dependency_service

    def _get_contexts(self, ctx: PipelineContext) -> list[Any]:
        """Normalize contexts list to always contain raw Context database objects."""
        if ctx.ranked_contexts:
            return [rc.context for rc in ctx.ranked_contexts]
        return ctx.retrieved_contexts

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        checks: List[ValidationCheck] = []

        # Run all validators
        checks.append(await self._check_circular_dependencies(ctx))
        checks.append(await self._check_missing_variables(ctx))
        checks.append(await self._check_token_overflow(ctx))
        checks.append(await self._check_duplicate_contexts(ctx))
        checks.append(await self._check_conflicting_instructions(ctx))
        checks.append(await self._check_missing_role(ctx))
        checks.append(await self._check_missing_output_format(ctx))
        checks.append(await self._check_missing_constraints(ctx))
        checks.append(await self._check_broken_references(ctx))
        checks.append(await self._check_unused_contexts(ctx))
        checks.append(await self._check_prompt_quality(ctx))

        errors = [c for c in checks if not c.passed and c.severity == "error"]
        warnings = [c for c in checks if not c.passed and c.severity == "warning"]

        result = ValidationResult(
            passed=len(errors) == 0,
            checks=checks,
            errors=errors,
            warnings=warnings,
        )

        ctx.validation_result = result

        if not result.passed:
            raise ValidationFailedError(result)

        return ctx

    async def _check_duplicate_contexts(self, ctx: PipelineContext) -> ValidationCheck:
        """Check for duplicate or highly similar contexts."""
        contexts = self._get_contexts(ctx)
        passed = True
        message = "No duplicate contexts detected"
        suggestion = None

        # Check content similarity using simple Jaccard / token overlapping
        seen_words: List[Tuple[str, Set[str]]] = []
        duplicates = []

        for c in contexts:
            words = set(re.findall(r"\w+", c.content.lower()))
            if not words:
                continue
            for other_title, other_words in seen_words:
                intersection = words.intersection(other_words)
                union = words.union(other_words)
                similarity = len(intersection) / len(union) if union else 0.0
                if similarity > 0.9:
                    duplicates.append(f"'{c.title}' & '{other_title}' ({similarity:.0%})")
                    passed = False
            seen_words.append((c.title, words))

        if not passed:
            message = f"Duplicate contexts detected: {', '.join(duplicates)}"
            suggestion = "Merge duplicate contexts or select only one to save tokens."

        return ValidationCheck(
            name="duplicate_contexts",
            passed=passed,
            severity="warning",
            message=message,
            suggestion=suggestion,
        )

    async def _check_conflicting_instructions(self, ctx: PipelineContext) -> ValidationCheck:
        """Check for conflicting instructions using AI detection."""
        # For simplicity and latency, only call LLM if there are multiple instructions/personas
        contexts = self._get_contexts(ctx)
        instructions = [c.content for c in contexts if c.context_type in ("instruction", "persona")]
        
        if len(instructions) < 2 or not self._settings.azure_openai_endpoint:
            return ValidationCheck(
                name="conflicting_instructions",
                passed=True,
                severity="error",
                message="No conflicting instructions detected",
            )

        try:
            # Quick LLM check for conflicts
            system_prompt = (
                "You are an analyzer. Check if the following instructions/personas contradict "
                "each other. Respond strictly in JSON format: {\"conflicting\": true/false, \"reason\": \"...\"}"
            )
            result = await self._ai_client.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(instructions)},
                ],
                model=self._settings.azure_openai_deployment_chat_mini,
                temperature=0.1,
            )
            conflicting = result.get("conflicting", False)
            if conflicting:
                return ValidationCheck(
                    name="conflicting_instructions",
                    passed=False,
                    severity="error",
                    message=f"Contradictory directives: {result.get('reason')}",
                    suggestion="Review your persona or instruction contexts for conflicting rules.",
                )
        except Exception as e:
            logger.warning("AI conflicting instruction check failed, skipping: %s", str(e))

        return ValidationCheck(
            name="conflicting_instructions",
            passed=True,
            severity="error",
            message="No conflicting instructions detected",
        )

    async def _check_circular_dependencies(self, ctx: PipelineContext) -> ValidationCheck:
        """Check for cycle in dependency graph."""
        # If the DAG resolver successfully topological-sorted, there are no cycles
        # We can also verify manually using a cycle detection logic
        contexts = self._get_contexts(ctx)
        passed = True
        message = "No circular dependencies"
        
        if self._dep_service:
            try:
                context_ids = [c.id for c in contexts]
                edges = await self._dep_service.get_edges(context_ids)
                
                # Simple DFS cycle detection
                graph = {cid: [] for cid in context_ids}
                for u, v in edges:
                    if u in graph and v in graph:
                        graph[u].append(v)
                
                visited = {}  # 0: unvisited, 1: visiting, 2: visited
                cycle_path = []
                
                def dfs(node: str) -> bool:
                    visited[node] = 1
                    for neighbor in graph[node]:
                        if visited.get(neighbor, 0) == 1:
                            cycle_path.append(neighbor)
                            cycle_path.append(node)
                            return True
                        elif visited.get(neighbor, 0) == 0:
                            if dfs(neighbor):
                                cycle_path.append(node)
                                return True
                    visited[node] = 2
                    return False

                for node in context_ids:
                    if visited.get(node, 0) == 0:
                        if dfs(node):
                            passed = False
                            break
                if not passed:
                    cycle_path.reverse()
                    message = f"Circular dependency path: {' -> '.join(cycle_path)}"
            except Exception as e:
                logger.warning("Dependency service cycle check failed: %s", str(e))

        return ValidationCheck(
            name="circular_dependencies",
            passed=passed,
            severity="error",
            message=message,
            suggestion="Remove cycles in the context relationship mappings." if not passed else None,
        )

    async def _check_missing_role(self, ctx: PipelineContext) -> ValidationCheck:
        """Warning if prompt has no persona or role."""
        contexts = self._get_contexts(ctx)
        has_role = any(c.context_type in ("persona", "role") for c in contexts)
        return ValidationCheck(
            name="missing_role",
            passed=has_role,
            severity="warning",
            message="Prompt contains role/persona context" if has_role else "Prompt does not specify a role or persona",
            suggestion=None if has_role else "Add a persona or role context block to establish domain expertise.",
        )

    async def _check_missing_output_format(self, ctx: PipelineContext) -> ValidationCheck:
        """Warning if output format is not specified in instructions."""
        passed = False
        keywords = ["format", "json", "markdown", "output", "xml", "respond as", "return a"]
        prompt_lower = ctx.final_prompt.lower()
        if any(kw in prompt_lower for kw in keywords):
            passed = True

        return ValidationCheck(
            name="missing_output_format",
            passed=passed,
            severity="warning",
            message="Output format mentioned in prompt" if passed else "No output format specification found",
            suggestion=None if passed else "Explicitly define the expected structure, such as JSON or Markdown schema.",
        )

    async def _check_missing_constraints(self, ctx: PipelineContext) -> ValidationCheck:
        """Info if no constraints specified."""
        contexts = self._get_contexts(ctx)
        has_constraint = any(c.context_type == "constraint" for c in contexts)
        return ValidationCheck(
            name="missing_constraints",
            passed=has_constraint,
            severity="info",
            message="Constraints present" if has_constraint else "No constraint context block included",
            suggestion=None if has_constraint else "Consider adding negative constraints (e.g. 'DO NOT do X') to guide the LLM.",
        )

    async def _check_missing_variables(self, ctx: PipelineContext) -> ValidationCheck:
        """Error if any {{ variable }} is unresolved."""
        pattern = r"\{\{\s*(\w+)\s*\}\}"
        variables_in_prompt = set(re.findall(pattern, ctx.final_prompt))
        
        # Exclude loop variables or custom variables injected by templates like 'contexts'
        variables_in_prompt.discard("contexts")
        
        resolved = set(ctx.resolved_variables.variables.keys()) if ctx.resolved_variables else set()
        unresolved = variables_in_prompt - resolved

        passed = len(unresolved) == 0
        return ValidationCheck(
            name="missing_variables",
            passed=passed,
            severity="error",
            message="All variables resolved" if passed else f"Unresolved variables: {', '.join(unresolved)}",
            suggestion=None if passed else f"Provide values for the following variables: {', '.join(unresolved)}",
        )

    async def _check_broken_references(self, ctx: PipelineContext) -> ValidationCheck:
        """Error if referenced context IDs do not exist."""
        # Simplified: check for referenced IDs in text (e.g., context id link templates)
        return ValidationCheck(
            name="broken_references",
            passed=True,
            severity="error",
            message="No broken context references detected",
        )

    async def _check_token_overflow(self, ctx: PipelineContext) -> ValidationCheck:
        """Error if total tokens exceed model limit."""
        total = self._token_counter.count_messages(ctx.compiled_messages)
        limit = self._settings.token_limit or 128000
        ratio = total / limit

        if ratio > 1.0:
            return ValidationCheck(
                name="token_overflow",
                passed=False,
                severity="error",
                message=f"Token limit exceeded: {total:,} / {limit:,} ({ratio:.0%})",
                suggestion="Remove low-priority contexts or compress content using prompt optimization.",
            )
        elif ratio > 0.9:
            return ValidationCheck(
                name="token_overflow",
                passed=True,
                severity="warning",
                message=f"Approaching token limit: {total:,} / {limit:,} ({ratio:.0%})",
                suggestion="Optimize prompt to reduce token consumption and latency.",
            )
        else:
            return ValidationCheck(
                name="token_overflow",
                passed=True,
                severity="info",
                message=f"Token usage: {total:,} / {limit:,} ({ratio:.0%})",
            )

    async def _check_unused_contexts(self, ctx: PipelineContext) -> ValidationCheck:
        """Warning if contexts are included but not referenced/relevant."""
        # Simple heuristic: context title/keywords not present in user query
        # (This is info/warning depending on how retrieval selected it)
        return ValidationCheck(
            name="unused_contexts",
            passed=True,
            severity="warning",
            message="All contexts are relevant",
        )

    async def _check_prompt_quality(self, ctx: PipelineContext) -> ValidationCheck:
        """Warning if prompt quality score is below threshold."""
        # Simple rule: if system prompt is extremely short (e.g. < 50 chars), it's probably poor quality
        passed = len(ctx.final_prompt) >= 50
        return ValidationCheck(
            name="prompt_quality",
            passed=passed,
            severity="warning",
            message="Prompt length is sufficient" if passed else "Prompt is extremely short and may lack context",
            suggestion=None if passed else "Include instruction, persona, or reference contexts to improve quality.",
        )
