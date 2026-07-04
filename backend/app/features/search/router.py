"""Search feature API router endpoints."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.database import get_session
from app.ai.client import AzureAIClient
from app.ai.embeddings import EmbeddingService
from app.ai.pipeline.retrieval import RetrievalEngine
from app.features.search.schemas import SearchResponse, SearchResultItem
from app.models import Template, Conversation

logger = logging.getLogger("pocket.features.search.router")

router = APIRouter()


def _compute_simple_score(query: str, title: str, body: str | None) -> float:
    """Helper to calculate a relevance score between 0.0 and 1.0 for non-FTS entities."""
    q = query.strip().lower()
    t = title.lower()
    b = (body or "").lower()
    
    if not q:
        return 0.0
    if q == t:
        return 1.0
    elif q in t:
        return 0.8
    elif q in b:
        return 0.5
    return 0.0


@router.get(
    "",
    response_model=SearchResponse,
    summary="Hybrid search across contexts, templates, and conversations",
)
async def hybrid_search(
    workspace_id: str,
    q: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> SearchResponse:
    """Search for relevant contexts (via hybrid engine), templates, and conversations."""
    if not q.strip():
        return SearchResponse(results=[])

    settings = Settings()
    ai_client = AzureAIClient(settings)
    embedding_service = EmbeddingService(ai_client, settings)
    retrieval_engine = RetrievalEngine(ai_client, embedding_service, settings)

    # 1. Search contexts via Hybrid Retrieval Engine
    contexts_results = await retrieval_engine.search(
        db=db,
        query=q,
        workspace_id=workspace_id,
        top_k=limit,
    )

    # 2. Search templates via case-insensitive pattern matching
    template_stmt = (
        select(Template)
        .where(
            Template.workspace_id == workspace_id,
            Template.deleted_at.is_(None),
            (Template.title.ilike(f"%{q}%") | Template.content.ilike(f"%{q}%") | Template.description.ilike(f"%{q}%"))
        )
        .limit(limit)
    )
    template_res = await db.execute(template_stmt)
    templates = template_res.scalars().all()

    # 3. Search conversations via case-insensitive pattern matching
    conversation_stmt = (
        select(Conversation)
        .where(
            Conversation.workspace_id == workspace_id,
            Conversation.deleted_at.is_(None),
            (Conversation.title.ilike(f"%{q}%") | Conversation.summary.ilike(f"%{q}%"))
        )
        .limit(limit)
    )
    conversation_res = await db.execute(conversation_stmt)
    conversations = conversation_res.scalars().all()

    results: list[SearchResultItem] = []

    # Map context results
    for r in contexts_results:
        results.append(
            SearchResultItem(
                id=r.context.id,
                title=r.context.title,
                type="context",
                score=r.final_score,
                subtitle=r.context.context_type,
                description=r.context.content[:150] + "..." if len(r.context.content) > 150 else r.context.content,
            )
        )

    # Map templates
    for t in templates:
        score = _compute_simple_score(q, t.title, t.description or t.content)
        if score > 0:
            results.append(
                SearchResultItem(
                    id=t.id,
                    title=t.title,
                    type="template",
                    score=score,
                    subtitle="Template",
                    description=t.description or (t.content[:150] + "..." if len(t.content) > 150 else t.content),
                )
            )

    # Map conversations
    for c in conversations:
        score = _compute_simple_score(q, c.title, c.summary)
        if score > 0:
            results.append(
                SearchResultItem(
                    id=c.id,
                    title=c.title,
                    type="conversation",
                    score=score,
                    subtitle=f"Conversation ({c.model})",
                    description=c.summary or "No summary available",
                )
            )

    # Sort consolidated results by score descending
    results.sort(key=lambda item: item.score, reverse=True)
    
    return SearchResponse(results=results[:limit])
