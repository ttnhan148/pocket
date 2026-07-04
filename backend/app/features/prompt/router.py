"""Prompt compile API endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.database import get_session
from app.ai.client import AzureAIClient
from app.ai.embeddings import EmbeddingService
from app.ai.pipeline.retrieval import RetrievalEngine
from app.ai.pipeline.ranking import RankingEngine
from app.ai.pipeline.token_counter import TokenCounter
from app.ai.pipeline import PipelineInput, PipelineOrchestrator
from app.features.prompt.schemas import PromptCompileRequest, PromptCompileResponse

router = APIRouter()


@router.post(
    "/compile",
    response_model=PromptCompileResponse,
    summary="Compile a prompt without execution",
)
async def compile_prompt(
    data: PromptCompileRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> PromptCompileResponse:
    """Runs the prompt pipeline up to optimization and scoring, returning compiled preview."""
    settings = Settings()
    ai_client = AzureAIClient(settings)
    token_counter = TokenCounter(settings)
    embedding_service = EmbeddingService(ai_client, settings)
    retrieval_engine = RetrievalEngine(ai_client, embedding_service, settings)
    ranking_engine = RankingEngine()

    orchestrator = PipelineOrchestrator(
        db=db,
        settings=settings,
        ai_client=ai_client,
        token_counter=token_counter,
        retrieval_engine=retrieval_engine,
        ranking_engine=ranking_engine,
    )

    input_payload = PipelineInput(
        user_message=data.user_message,
        workspace_id=data.workspace_id,
        selected_context_ids=data.selected_context_ids,
        variable_overrides=data.variable_overrides,
    )

    ctx = await orchestrator.compile_only(input_payload)

    # Map Validation Result details
    val_res = None
    if ctx.validation_result:
        val_res = {
            "passed": ctx.validation_result.passed,
            "errors": [
                {
                    "name": e.name,
                    "passed": e.passed,
                    "severity": e.severity,
                    "message": e.message,
                    "suggestion": e.suggestion,
                }
                for e in ctx.validation_result.errors
            ],
            "warnings": [
                {
                    "name": w.name,
                    "passed": w.passed,
                    "severity": w.severity,
                    "message": w.message,
                    "suggestion": w.suggestion,
                }
                for w in ctx.validation_result.warnings
            ],
        }

    # Map Prompt Score details
    score_res = None
    if ctx.prompt_score:
        score_res = {
            "overall": ctx.prompt_score.overall,
            "clarity": ctx.prompt_score.clarity,
            "specificity": ctx.prompt_score.specificity,
            "completeness": ctx.prompt_score.completeness,
            "consistency": ctx.prompt_score.consistency,
            "efficiency": ctx.prompt_score.efficiency,
            "reasoning": ctx.prompt_score.reasoning,
            "suggestions": ctx.prompt_score.suggestions,
        }

    return PromptCompileResponse(
        final_prompt=ctx.final_prompt,
        system_prompt=ctx.system_prompt,
        variables_resolved=ctx.resolved_variables.variables if ctx.resolved_variables else {},
        validation_result=val_res,
        prompt_score=score_res,
    )


@router.post(
    "/{id}/benchmark",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Benchmark a prompt run and generate alternatives",
)
async def benchmark_prompt(
    id: str,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Trigger a background AI job to compare compiled prompt against generated alternatives."""
    from app.features.jobs.service import AIJobService
    from app.features.jobs.runner import run_prompt_benchmark
    from app.models.prompt import PromptRun
    from app.core.exceptions import NotFoundError
    from sqlalchemy import select

    # Verify prompt run exists
    stmt = select(PromptRun).where(PromptRun.id == id)
    pr = (await db.execute(stmt)).scalar_one_or_none()
    if not pr:
        raise NotFoundError("PromptRun", id)

    # Create job
    job_service = AIJobService(db)
    job = await job_service.create_job(job_type="review", input_data={"prompt_run_id": id})
    
    # Run task in background
    background_tasks.add_task(run_prompt_benchmark, job.id, id)

    return {"job_id": job.id, "status": "pending"}
