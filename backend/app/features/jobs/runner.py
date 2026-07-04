"""Background runners for AI jobs (M42, M43)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import Settings
from app.ai.client import AzureAIClient
from app.core import database as db_core
from app.features.jobs.service import AIJobService
from app.models.prompt import PromptRun

logger = logging.getLogger("pocket.features.jobs.runner")


async def run_prompt_benchmark(job_id: str, prompt_run_id: str) -> None:
    """Run prompt benchmark asynchronously and save comparison result."""
    if db_core._session_factory is None:
        logger.error("Database session factory not initialized.")
        return

    async with db_core._session_factory() as db:
        job_service = AIJobService(db)
        settings = Settings()
        ai_client = AzureAIClient(settings)

        try:
            await job_service.start_job(job_id)
            await job_service.update_progress(job_id, 0.2)

            # 1. Fetch original PromptRun
            stmt = select(PromptRun).where(PromptRun.id == prompt_run_id)
            prompt_run = (await db.execute(stmt)).scalar_one_or_none()
            if not prompt_run:
                raise ValueError(f"PromptRun {prompt_run_id} not found")

            await job_service.update_progress(job_id, 0.4)

            # 2. Call AI to benchmark
            if not settings.azure_openai_endpoint:
                # Mock result when endpoint is not configured
                comparison_data = {
                    "alternative_prompt": f"[OPTIMIZED] {prompt_run.compiled_prompt}",
                    "original_scores": {
                        "clarity": 0.8,
                        "specificity": 0.7,
                        "completeness": 0.8,
                        "consistency": 0.9,
                        "efficiency": 0.6,
                    },
                    "alternative_scores": {
                        "clarity": 0.9,
                        "specificity": 0.85,
                        "completeness": 0.9,
                        "consistency": 0.9,
                        "efficiency": 0.8,
                    },
                    "comparison_summary": "Alternative prompt has better clarity and optimized token usage.",
                }
            else:
                system_prompt = (
                    "You are an expert AI prompt engineer and evaluator.\n"
                    "You will compare an existing compiled prompt with an alternative version that you will generate to optimize its clarity, specificity, and efficiency.\n"
                    "You MUST return a JSON object with the exact fields:\n"
                    "- alternative_prompt: the optimized/improved prompt content\n"
                    "- original_scores: an object containing float scores (0.0 to 1.0) for: clarity, specificity, completeness, consistency, efficiency\n"
                    "- alternative_scores: an object containing float scores (0.0 to 1.0) for: clarity, specificity, completeness, consistency, efficiency\n"
                    "- comparison_summary: a concise comparison and explanation of why the alternative is better (or if they are equal)\n"
                )

                user_content = (
                    f"Original Compiled Prompt:\n{prompt_run.compiled_prompt}\n\n"
                    f"User Input Context:\n{prompt_run.user_input}\n"
                )

                comparison_data = await ai_client.chat_json(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    model=settings.azure_openai_deployment_chat,
                )

            await job_service.update_progress(job_id, 0.8)

            # 3. Save result
            await job_service.add_result(
                job_id=job_id,
                result_type="prompt_benchmark",
                result_data=comparison_data,
                entity_type="prompt_run",
                entity_id=prompt_run_id,
            )

            await job_service.update_progress(job_id, 1.0, status="completed")
            await db.commit()

        except Exception as e:
            logger.exception(f"Error executing prompt benchmark job {job_id}")
            try:
                await job_service.update_progress(job_id, 1.0, status="failed", error_message=str(e))
                await db.commit()
            except Exception as inner_e:
                logger.error(f"Failed to save job failure status: {inner_e}")


async def run_context_health_check(job_id: str, workspace_id: str) -> None:
    """Evaluate health for all contexts in a workspace asynchronously and store scores."""
    import math
    from datetime import datetime, timezone, timedelta
    from app.models import Context, ContextHealthScore, PromptContext, ContextUsage
    from sqlalchemy import func

    if db_core._session_factory is None:
        logger.error("Database session factory not initialized.")
        return

    async with db_core._session_factory() as db:
        job_service = AIJobService(db)

        try:
            await job_service.start_job(job_id)
            await job_service.update_progress(job_id, 0.1)

            # 1. Fetch active contexts
            stmt = select(Context).where(
                Context.workspace_id == workspace_id,
                Context.deleted_at.is_(None),
                Context.is_archived == 0,
            )
            contexts = list((await db.execute(stmt)).scalars().all())

            if not contexts:
                await job_service.update_progress(job_id, 1.0, status="completed")
                await db.commit()
                return

            now = datetime.now(timezone.utc)
            total = len(contexts)
            completed_count = 0

            # 2. Iterate and evaluate each context
            for ctx in contexts:
                # Freshness Score: decay function based on days since last update
                # (1.0 if updated today, decaying to ~0.37 at 30 days)
                days_since_update = (now - ctx.updated_at.replace(tzinfo=timezone.utc)).days
                freshness_score = math.exp(-days_since_update / 30.0)

                # Usage Score: count uses in prompt_contexts or context_usages in last 30 days
                limit_date = now - timedelta(days=30)
                
                # Fetch uses from PromptContext associated with active PromptRuns in last 30 days
                stmt_usages = select(func.count(PromptContext.id)).join(
                    PromptRun, PromptRun.id == PromptContext.prompt_run_id
                ).where(
                    PromptContext.context_id == ctx.id,
                    PromptRun.created_at >= limit_date
                )
                usages_res = await db.execute(stmt_usages)
                usage_count_30 = usages_res.scalar() or 0
                usage_score = min(1.0, math.log(usage_count_30 + 1) / math.log(10))

                # Quality Score: uses context.confidence as base quality score
                quality_score = ctx.confidence

                # Relevance Score: average relevance_score in PromptContext, defaulting to 1.0 if unused
                stmt_relevance = select(func.avg(PromptContext.relevance_score)).where(
                    PromptContext.context_id == ctx.id,
                    PromptContext.relevance_score.is_not(None)
                )
                relevance_res = await db.execute(stmt_relevance)
                avg_relevance = relevance_res.scalar()
                relevance_score = float(avg_relevance) if avg_relevance is not None else 1.0

                # Overall Health
                overall_health = (freshness_score + usage_score + quality_score + relevance_score) / 4.0

                # Evaluate issues & recommendations
                issues = []
                recommendations = []

                if freshness_score < 0.5:
                    issues.append("stale")
                    recommendations.append("This context has not been updated recently. Consider reviewing it.")
                if usage_score < 0.2:
                    issues.append("low_usage")
                    recommendations.append("This context is rarely used. Consider archiving it to reduce noise.")
                if quality_score < 0.7:
                    issues.append("low_quality")
                    recommendations.append("The content quality or confidence score is low. Please review and improve.")

                # Save score record
                health_record = ContextHealthScore(
                    context_id=ctx.id,
                    overall_health=overall_health,
                    freshness_score=freshness_score,
                    usage_score=usage_score,
                    quality_score=quality_score,
                    relevance_score=relevance_score,
                    issues=json.dumps(issues),
                    recommendations=json.dumps(recommendations),
                    evaluated_at=now,
                )
                db.add(health_record)

                completed_count += 1
                progress = 0.1 + (0.8 * (completed_count / total))
                await job_service.update_progress(job_id, progress)

            # 3. Add job result summary
            await job_service.add_result(
                job_id=job_id,
                result_type="context_health_summary",
                result_data={"evaluated_contexts": total, "timestamp": now.isoformat()},
                entity_type="workspace",
                entity_id=workspace_id,
            )

            await job_service.update_progress(job_id, 1.0, status="completed")
            await db.commit()

        except Exception as e:
            logger.exception(f"Error executing context health check job {job_id}")
            try:
                await job_service.update_progress(job_id, 1.0, status="failed", error_message=str(e))
                await db.commit()
            except Exception as inner_e:
                logger.error(f"Failed to save job failure status: {inner_e}")

