"""Full 18-step AI Prompt Pipeline Orchestrator."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import AzureAIClient
from app.ai.pipeline.base import (
    Conflict,
    ContextUsed,
    PipelineContext,
    PipelineInput,
    PipelineOutput,
    PipelineStep,
    PipelineStepError,
    PipelineStepTrace,
    ResolvedVariables,
    TokenUsage,
    ValidationFailedError,
)
from app.ai.pipeline.compiler import PromptCompiler
from app.ai.pipeline.critic import PromptCritic
from app.ai.pipeline.enhancer import PromptEnhancer
from app.ai.pipeline.intent import IntentDetector
from app.ai.pipeline.optimizer import PromptOptimizer
from app.ai.pipeline.ranking import RankingEngine
from app.ai.pipeline.retrieval import RetrievalEngine
from app.ai.pipeline.scorer import PromptScorer
from app.ai.pipeline.token_counter import TokenCounter
from app.ai.pipeline.validator import ValidationEngine
from app.config import Settings
from app.features.variables.service import VariableService
from app.features.workspace.service import WorkspaceService
from app.models import Context, ContextDependency, Workspace

logger = logging.getLogger("pocket.ai.pipeline.orchestrator")


class WorkspaceDetector(PipelineStep):
    """Step 3: Workspace Detection."""
    name = "workspace_detection"

    def __init__(self, workspace_service: WorkspaceService) -> None:
        self._workspace_service = workspace_service

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        # If workspace_id is provided in input, retrieve it. Otherwise load first workspace.
        workspace_id = ctx.input.workspace_id
        if workspace_id:
            ctx.workspace = await self._workspace_service.get_workspace(workspace_id)
        else:
            workspaces = await self._workspace_service.list_workspaces(limit=1)
            if workspaces:
                ctx.workspace = workspaces[0]
            else:
                raise PipelineStepError("No workspaces found in the system.")
        return ctx

    def summarize_input(self, ctx: PipelineContext) -> str:
        return f"Input workspace_id: {ctx.input.workspace_id}"

    def summarize_output(self, ctx: PipelineContext) -> str:
        return f"Detected Workspace: {ctx.workspace.name if ctx.workspace else 'None'}"


class VariableResolverStep(PipelineStep):
    """Step 4: Variable Resolution Adapter."""
    name = "variable_resolution"

    def __init__(self, variable_service: VariableService) -> None:
        self._variable_service = variable_service

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.workspace:
            raise PipelineStepError("Workspace must be detected before variable resolution.")

        # Resolve variables using the service priority chain
        resolved = await self._variable_service.resolve_variables(
            workspace_id=ctx.workspace.id,
            runtime_vars=ctx.input.variable_overrides,
        )

        variables_dict = {k: str(v.value) for k, v in resolved.items() if v.value is not None}
        unresolved = [k for k, v in resolved.items() if v.value is None]
        source_map = {k: v.source for k, v in resolved.items()}

        ctx.resolved_variables = ResolvedVariables(
            variables=variables_dict,
            unresolved=unresolved,
            source_map=source_map,
        )
        return ctx

    def summarize_input(self, ctx: PipelineContext) -> str:
        return f"Workspace ID: {ctx.workspace.id if ctx.workspace else 'None'}"

    def summarize_output(self, ctx: PipelineContext) -> str:
        count = len(ctx.resolved_variables.variables) if ctx.resolved_variables else 0
        return f"Resolved {count} variables"


class DependencyResolver(PipelineStep):
    """Step 6: Dependency Resolution (DAG / Topological Sort)."""
    name = "dependency_resolution"

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        # Retrieve starting contexts
        contexts = list(ctx.retrieved_contexts)
        context_ids = [c.id for c in contexts]

        if not context_ids:
            ctx.ordered_contexts = []
            return ctx

        # 1. Fetch all dependencies (edges) for retrieved contexts
        stmt = select(ContextDependency).where(
            ContextDependency.source_id.in_(context_ids),
            ContextDependency.deleted_at.is_(None)
        )
        res = await self._db.execute(stmt)
        edges = list(res.scalars().all())

        # 2. Add missing dependency target contexts recursively
        visited_ids = set(context_ids)
        to_fetch = [e.target_id for e in edges if e.target_id not in visited_ids]

        if to_fetch:
            stmt_ctx = select(Context).where(
                Context.id.in_(to_fetch),
                Context.deleted_at.is_(None)
            )
            res_ctx = await self._db.execute(stmt_ctx)
            fetched_contexts = res_ctx.scalars().all()
            contexts.extend(fetched_contexts)
            
            # Update edges with new nodes
            all_ids = [c.id for c in contexts]
            stmt_all_edges = select(ContextDependency).where(
                ContextDependency.source_id.in_(all_ids),
                ContextDependency.deleted_at.is_(None)
            )
            res_all_edges = await self._db.execute(stmt_all_edges)
            edges = list(res_all_edges.scalars().all())

        # Filter valid edges that exist within our nodes
        active_ids = {c.id for c in contexts}
        valid_edges = [e for e in edges if e.target_id in active_ids]

        # 3. Topological Sort (Kahn's Algorithm)
        # B depends on A (B -> A). A must come before B.
        adj = defaultdict(list)
        indegree = {cid: 0 for cid in active_ids}
        
        for e in valid_edges:
            adj[e.target_id].append(e.source_id)
            indegree[e.source_id] += 1

        queue = deque([cid for cid in active_ids if indegree[cid] == 0])
        sorted_ids = []

        while queue:
            curr = queue.popleft()
            sorted_ids.append(curr)
            for neighbor in adj[curr]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_ids) != len(active_ids):
            # Cyclic path detected
            remaining = [cid for cid in active_ids if cid not in sorted_ids]
            raise PipelineStepError(f"Circular dependency detected between contexts: {remaining}")

        id_to_context = {c.id: c for c in contexts}
        ctx.ordered_contexts = [id_to_context[cid] for cid in sorted_ids]
        return ctx

    def summarize_input(self, ctx: PipelineContext) -> str:
        return f"Retrieved Contexts: {len(ctx.retrieved_contexts)}"

    def summarize_output(self, ctx: PipelineContext) -> str:
        return f"Ordered Contexts: {len(ctx.ordered_contexts)}"


class ConflictDetector(PipelineStep):
    """Step 7: Conflict Detection & Resolution."""
    name = "conflict_detection"

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        contexts = list(ctx.ordered_contexts)
        conflicts: List[Conflict] = []

        # Rule 1: Only one persona allowed
        personas = [c for c in contexts if c.context_type == "persona"]
        if len(personas) > 1:
            # Resolve conflict: Keep the first one, discard the others
            keep = personas[0]
            to_discard = personas[1:]
            for d in to_discard:
                conflicts.append(Conflict(
                    context_a_id=keep.id,
                    context_b_id=d.id,
                    conflict_type="duplicate",
                    description=f"Multiple personas: keeping '{keep.title}', discarding '{d.title}'",
                    resolution="keep_a"
                ))
                if d in contexts:
                    contexts.remove(d)

        # Update contexts in context state
        ctx.conflicts = conflicts
        ctx.ordered_contexts = contexts
        return ctx

    def summarize_input(self, ctx: PipelineContext) -> str:
        return f"Ordered Contexts: {len(ctx.ordered_contexts)}"

    def summarize_output(self, ctx: PipelineContext) -> str:
        return f"Conflicts: {len(ctx.conflicts)}, Filtered Contexts: {len(ctx.ordered_contexts)}"


class HybridRetrievalAdapter(PipelineStep):
    """Step 5: Hybrid Retrieval Adapter."""
    name = "hybrid_retrieval"

    def __init__(self, db: AsyncSession, retrieval_engine: RetrievalEngine) -> None:
        self._db = db
        self._retrieval_engine = retrieval_engine

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.workspace:
            raise PipelineStepError("Workspace must be detected before retrieval.")

        if ctx.input.selected_context_ids:
            # Load user-selected contexts explicitly
            stmt = select(Context).where(
                Context.id.in_(ctx.input.selected_context_ids),
                Context.deleted_at.is_(None)
            )
            res = await self._db.execute(stmt)
            ctx.retrieved_contexts = list(res.scalars().all())
        else:
            # Auto-retrieve relevant contexts
            results = await self._retrieval_engine.search(
                db=self._db,
                query=ctx.input.user_message,
                workspace_id=ctx.workspace.id,
                intent=ctx.intent,
            )
            ctx.retrieved_contexts = [r.context for r in results]

        return ctx

    def summarize_input(self, ctx: PipelineContext) -> str:
        return f"Query: {ctx.input.user_message[:30]}..."

    def summarize_output(self, ctx: PipelineContext) -> str:
        return f"Retrieved: {len(ctx.retrieved_contexts)} contexts"


class ContextRankingAdapter(PipelineStep):
    """Step 8: Context Ranking Adapter."""
    name = "context_ranking"

    def __init__(self, ranking_engine: RankingEngine) -> None:
        self._ranking_engine = ranking_engine

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        # Wrap contexts as RetrievalResult mocks to match ranking rank interface
        from app.ai.pipeline.retrieval import RetrievalResult
        
        results = []
        for c in ctx.ordered_contexts:
            results.append(RetrievalResult(
                context=c,
                fts_score=0.5,
                fuzzy_score=0.5,
                semantic_score=0.5,
                metadata_score=0.5,
                final_score=0.5
            ))

        favorites = set()  # Favorites can be populated if required
        ctx.ranked_contexts = self._ranking_engine.rank(
            results=results,
            workspace_id=ctx.workspace.id if ctx.workspace else "",
            favorites=favorites
        )
        return ctx

    def summarize_input(self, ctx: PipelineContext) -> str:
        return f"Ordered Contexts: {len(ctx.ordered_contexts)}"

    def summarize_output(self, ctx: PipelineContext) -> str:
        return f"Ranked Contexts: {len(ctx.ranked_contexts)}"


class PipelineOrchestrator:
    """Orchestrates the entire 18-step AI prompt pipeline."""

    def __init__(
        self,
        db: AsyncSession,
        settings: Settings,
        ai_client: AzureAIClient,
        token_counter: TokenCounter,
        retrieval_engine: RetrievalEngine,
        ranking_engine: RankingEngine,
    ) -> None:
        self._db = db
        self._settings = settings
        self._ai_client = ai_client
        self._token_counter = token_counter

        # Initialize Services
        self._workspace_service = WorkspaceService(db)
        self._variable_service = VariableService(db)

        # Initialize Pipeline Steps
        self._intent_detector = IntentDetector(ai_client, settings)
        self._workspace_detector = WorkspaceDetector(self._workspace_service)
        self._variable_resolver = VariableResolverStep(self._variable_service)
        self._retrieval_adapter = HybridRetrievalAdapter(db, retrieval_engine)
        self._dep_resolver = DependencyResolver(db)
        self._conflict_detector = ConflictDetector()
        self._ranking_adapter = ContextRankingAdapter(ranking_engine)
        self._compiler = PromptCompiler()
        self._validator = ValidationEngine(ai_client, token_counter, settings)
        self._optimizer = PromptOptimizer(ai_client, settings)
        self._enhancer = PromptEnhancer(ai_client, settings)
        self._critic = PromptCritic(ai_client, settings)
        self._scorer = PromptScorer(ai_client, settings)

        # Ordered pipeline steps
        self._steps: List[PipelineStep] = [
            self._intent_detector,      # Step 2
            self._workspace_detector,   # Step 3
            self._variable_resolver,    # Step 4
            self._retrieval_adapter,    # Step 5
            self._dep_resolver,         # Step 6
            self._conflict_detector,    # Step 7
            self._ranking_adapter,      # Step 8
            self._compiler,             # Step 9
            self._validator,            # Step 10
            self._optimizer,            # Step 11
            self._enhancer,             # Step 12
            self._critic,               # Step 13
            self._scorer,               # Step 14
        ]

    async def execute(self, input: PipelineInput) -> PipelineOutput:
        trace: List[PipelineStepTrace] = []
        ctx = PipelineContext(input=input)

        start_time = time.monotonic()

        for step in self._steps:
            step_start = time.monotonic()
            try:
                ctx = await step.execute(ctx)
                duration = int((time.monotonic() - step_start) * 1000)
                trace.append(PipelineStepTrace(
                    step_name=step.name,
                    input_summary=step.summarize_input(ctx),
                    output_summary=step.summarize_output(ctx),
                    duration_ms=duration,
                    status="success"
                ))
            except ValidationFailedError as e:
                # Validation error halts pipeline immediately (compiler blocker)
                duration = int((time.monotonic() - step_start) * 1000)
                trace.append(PipelineStepTrace(
                    step_name=step.name,
                    input_summary="",
                    output_summary=f"Validation failed: {str(e)}",
                    duration_ms=duration,
                    status="failed"
                ))
                return PipelineOutput(
                    final_prompt="",
                    system_prompt="",
                    ai_response="",
                    validation_result=e.result,
                    pipeline_trace=trace,
                    latency_ms=int((time.monotonic() - start_time) * 1000)
                )
            except Exception as e:
                logger.error("Step %s failed with error: %s", step.name, str(e), exc_info=True)
                duration = int((time.monotonic() - step_start) * 1000)
                trace.append(PipelineStepTrace(
                    step_name=step.name,
                    input_summary="",
                    output_summary=f"Fallback triggered: {str(e)}",
                    duration_ms=duration,
                    status="fallback"
                ))
                ctx = step.fallback(ctx)

        # Step 16: Call Azure OpenAI completions
        ai_chat_start = time.monotonic()
        
        # Determine model
        model = ctx.selected_model or self._settings.azure_openai_deployment_chat
        
        try:
            res = await self._ai_client.chat(
                messages=ctx.compiled_messages,
                model=model,
            )
            ai_response = res.content
            prompt_tokens = res.prompt_tokens
            completion_tokens = res.completion_tokens
            total_tokens = res.total_tokens
            cost = res.cost
        except Exception as e:
            logger.error("LLM Chat generation step 16 failed: %s", str(e))
            ai_response = "Error calling Azure OpenAI completion service."
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            cost = 0.0

        ai_chat_duration = int((time.monotonic() - ai_chat_start) * 1000)
        trace.append(PipelineStepTrace(
            step_name="azure_openai_chat",
            input_summary=f"Model: {model}, Messages: {len(ctx.compiled_messages)}",
            output_summary=f"Response length: {len(ai_response)} chars",
            duration_ms=ai_chat_duration,
            status="success"
        ))

        # Contexts Used schema assembly
        contexts_used = []
        for rc in ctx.ranked_contexts:
            contexts_used.append(ContextUsed(
                id=rc.context.id,
                title=rc.context.title,
                score=rc.score
            ))

        total_latency = int((time.monotonic() - start_time) * 1000)

        return PipelineOutput(
            final_prompt=ctx.final_prompt,
            system_prompt=ctx.system_prompt,
            ai_response=ai_response,
            contexts_used=contexts_used,
            variables_resolved=ctx.resolved_variables.variables if ctx.resolved_variables else {},
            validation_result=ctx.validation_result,
            prompt_score=ctx.prompt_score,
            token_usage=TokenUsage(
                prompt=prompt_tokens,
                completion=completion_tokens,
                total=total_tokens
            ),
            cost=cost,
            latency_ms=total_latency,
            pipeline_trace=trace
        )

    async def compile_only(self, input: PipelineInput) -> PipelineContext:
        """Runs the pipeline up to scoring, skipping final Azure OpenAI completions step."""
        ctx = PipelineContext(input=input)
        for step in self._steps:
            try:
                ctx = await step.execute(ctx)
            except ValidationFailedError as e:
                ctx.validation_result = e.result
                break
            except Exception as e:
                logger.error("Step %s failed in compile_only: %s", step.name, str(e))
                ctx = step.fallback(ctx)
        return ctx

