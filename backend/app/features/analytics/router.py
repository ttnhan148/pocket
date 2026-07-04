"""APIs for Analytics Dashboard statistics and trends."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import Context, PromptRun

router = APIRouter()


class AnalyticsOverview(BaseModel):
    total_contexts: int
    total_prompts: int
    total_tokens: int
    total_cost: float


class DailyTrendItem(BaseModel):
    date: str
    tokens: int
    cost: float


class ContextUsageItem(BaseModel):
    id: str
    title: str
    context_type: str
    usage_count: int
    last_used_at: Optional[str] = None


@router.get(
    "/overview",
    response_model=AnalyticsOverview,
    summary="Get aggregated statistics overview",
)
async def get_overview(
    workspace_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> AnalyticsOverview:
    """Retrieve total count of contexts, compiled prompts, cumulative tokens, and cumulative cost."""
    # Contexts count
    stmt_ctx = select(func.count(Context.id)).where(
        Context.workspace_id == workspace_id,
        Context.deleted_at.is_(None),
    )
    res_ctx = await db.execute(stmt_ctx)
    total_contexts = res_ctx.scalar() or 0

    # PromptRuns aggregates
    stmt_runs = select(
        func.count(PromptRun.id),
        func.sum(PromptRun.total_tokens),
        func.sum(PromptRun.cost),
    ).where(PromptRun.workspace_id == workspace_id)
    res_runs = await db.execute(stmt_runs)
    row = res_runs.first()
    
    total_prompts = row[0] or 0
    total_tokens = row[1] or 0
    total_cost = float(row[2] or 0.0)

    return AnalyticsOverview(
        total_contexts=total_contexts,
        total_prompts=total_prompts,
        total_tokens=total_tokens,
        total_cost=total_cost,
    )


@router.get(
    "/trends",
    response_model=List[DailyTrendItem],
    summary="Get daily usage trends",
)
async def get_trends(
    workspace_id: str,
    days: int = 7,
    db: Annotated[AsyncSession, Depends(get_session)] = None,
) -> List[DailyTrendItem]:
    """Retrieve daily token usage and cost over the last N days."""
    since_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Query prompts grouped by date
    stmt = (
        select(
            func.strftime("%Y-%m-%d", func.datetime(PromptRun.created_at)),
            func.sum(PromptRun.total_tokens),
            func.sum(PromptRun.cost),
        )
        .where(
            PromptRun.workspace_id == workspace_id,
            PromptRun.created_at >= since_date,
        )
        .group_by(func.strftime("%Y-%m-%d", func.datetime(PromptRun.created_at)))
        .order_by(func.strftime("%Y-%m-%d", func.datetime(PromptRun.created_at)).asc())
    )
    res = await db.execute(stmt)
    rows = res.all()

    # Pre-populate dictionary for all requested days to handle empty days cleanly
    trend_dict = {}
    for i in range(days):
        d_str = (since_date + timedelta(days=i+1)).strftime("%Y-%m-%d")
        trend_dict[d_str] = {"tokens": 0, "cost": 0.0}

    for row in rows:
        d_str = row[0]
        if d_str in trend_dict:
            trend_dict[d_str] = {
                "tokens": int(row[1] or 0),
                "cost": float(row[2] or 0.0),
            }

    return [
        DailyTrendItem(date=k, tokens=v["tokens"], cost=v["cost"])
        for k, v in trend_dict.items()
    ]


@router.get(
    "/top-contexts",
    response_model=List[ContextUsageItem],
    summary="Get top used contexts",
)
async def get_top_contexts(
    workspace_id: str,
    limit: int = 5,
    db: Annotated[AsyncSession, Depends(get_session)] = None,
) -> List[ContextUsageItem]:
    """Retrieve contexts ordered by usage count descending."""
    stmt = (
        select(Context)
        .where(
            Context.workspace_id == workspace_id,
            Context.deleted_at.is_(None),
            Context.usage_count > 0,
        )
        .order_by(Context.usage_count.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    return [
        ContextUsageItem(
            id=c.id,
            title=c.title,
            context_type=c.context_type,
            usage_count=c.usage_count,
            last_used_at=c.last_used_at,
        )
        for c in res.scalars().all()
    ]


@router.get(
    "/dead-contexts",
    response_model=List[ContextUsageItem],
    summary="Get dead/unused contexts",
)
async def get_dead_contexts(
    workspace_id: str,
    limit: int = 10,
    db: Annotated[AsyncSession, Depends(get_session)] = None,
) -> List[ContextUsageItem]:
    """Retrieve contexts that have never been used or not used for a long time."""
    # Contexts with 0 usage count, or last_used_at older than 90 days
    limit_date = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    stmt = (
        select(Context)
        .where(
            Context.workspace_id == workspace_id,
            Context.deleted_at.is_(None),
            (Context.usage_count == 0) | (Context.last_used_at < limit_date),
        )
        .order_by(Context.usage_count.asc(), Context.created_at.asc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    return [
        ContextUsageItem(
            id=c.id,
            title=c.title,
            context_type=c.context_type,
            usage_count=c.usage_count,
            last_used_at=c.last_used_at,
        )
        for c in res.scalars().all()
    ]


class WeeklyReviewResponse(BaseModel):
    total_tokens: int
    total_cost: float
    total_prompts: int
    top_contexts: List[ContextUsageItem]
    dead_contexts: List[ContextUsageItem]
    recommendations: List[str]


@router.get(
    "/weekly-review",
    response_model=WeeklyReviewResponse,
    summary="Get weekly usage review and recommendations",
)
async def get_weekly_review(
    workspace_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> WeeklyReviewResponse:
    """Compile a weekly usage review including tokens, costs, top/dead contexts, and recommendations."""
    # 1. Stats in the last 7 days
    since_date = datetime.now(timezone.utc) - timedelta(days=7)
    
    stmt_runs = select(
        func.count(PromptRun.id),
        func.sum(PromptRun.total_tokens),
        func.sum(PromptRun.cost),
    ).where(
        PromptRun.workspace_id == workspace_id,
        PromptRun.created_at >= since_date,
    )
    res_runs = await db.execute(stmt_runs)
    row = res_runs.first()
    
    total_prompts = row[0] or 0
    total_tokens = row[1] or 0
    total_cost = float(row[2] or 0.0)

    # 2. Get Top Contexts
    top_ctxs = await get_top_contexts(workspace_id, limit=3, db=db)

    # 3. Get Dead Contexts
    dead_ctxs = await get_dead_contexts(workspace_id, limit=3, db=db)

    # 4. Generate Recommendations
    recs = []
    if dead_ctxs:
        recs.append(
            f"You have {len(dead_ctxs)} context(s) unused for over 90 days (e.g. '{dead_ctxs[0].title}'). "
            "Consider archiving or updating them."
        )
    if total_cost > 1.0:
        recs.append(
            f"Weekly API usage cost is ${total_cost:.4f}. "
            "Consider using gpt-4.1-mini to reduce expenses."
        )
    if total_prompts > 20:
        recs.append(
            "High frequency of prompt compilation detected. "
            "Save frequently used prompts as reusable templates."
        )
    if not recs:
        recs.append("Workspace health is optimal. Keep adding contexts to improve prompt relevance.")

    return WeeklyReviewResponse(
        total_tokens=total_tokens,
        total_cost=total_cost,
        total_prompts=total_prompts,
        top_contexts=top_ctxs,
        dead_contexts=dead_ctxs,
        recommendations=recs,
    )

