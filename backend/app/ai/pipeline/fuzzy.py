"""Fuzzy string matching on context titles and tags using RapidFuzz."""

from __future__ import annotations

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from rapidfuzz import fuzz, process

from app.models import Context

logger = logging.getLogger("pocket.ai.pipeline.fuzzy")


async def fuzzy_search(
    db: AsyncSession,
    query: str,
    workspace_id: str,
    limit: int = 50,
    score_cutoff: float = 60.0,
) -> list[tuple[str, float]]:
    """Perform fuzzy search on context titles and tags in a workspace.
    
    Returns a list of tuples containing (context_id, normalized_score)
    where normalized_score is between 0.0 and 1.0.
    """
    if not query.strip():
        return []

    # Get all active contexts in the workspace with tags eagerly loaded
    stmt = (
        select(Context)
        .options(selectinload(Context.tags))
        .where(
            Context.workspace_id == workspace_id,
            Context.deleted_at.is_(None),
        )
    )
    
    try:
        res = await db.execute(stmt)
        contexts = res.scalars().all()
        
        if not contexts:
            return []
            
        # Build choices dictionary: context_id -> string to match on (title + space-separated tags)
        choices = {}
        for c in contexts:
            tag_names = " ".join(t.name for t in c.tags)
            choices[c.id] = f"{c.title} {tag_names}".strip()
            
        # Extract matches using RapidFuzz WRatio (Weighted Ratio)
        results = process.extract(
            query,
            choices,
            scorer=fuzz.WRatio,
            limit=limit,
            score_cutoff=score_cutoff,
        )
        
        # RapidFuzz returns matches in format (value, score, key)
        # Score is 0-100, normalize it to 0.0 - 1.0
        return [(match[2], match[1] / 100.0) for match in results]
        
    except Exception as e:
        logger.error("Fuzzy search matching failed: %s", str(e), exc_info=True)
        return []
