"""SQLite FTS5 Full-Text Search helper with BM25 scoring."""

from __future__ import annotations

import logging
import re
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("pocket.ai.pipeline.search")


def prepare_fts_query(query: str) -> str:
    """Prepares a raw search query for FTS5 MATCH syntax.
    
    Filters out characters that could cause syntax errors and structures
    the query to require all words, allowing prefix matching on the last word.
    """
    # Clean special characters but preserve alphanumeric and whitespace
    clean = re.sub(r'[^\w\s]', ' ', query).strip()
    words = [w for w in clean.split() if w]
    if not words:
        return ""
        
    # Standard query: AND match on all words with a wildcard * on the last word for prefix match
    terms = []
    for i, word in enumerate(words):
        if i == len(words) - 1:
            terms.append(f"{word}*")
        else:
            terms.append(word)
            
    return " AND ".join(terms)


def normalize_bm25(score: float) -> float:
    """Normalizes SQLite BM25 score to a 0.0 - 1.0 range (higher is better).
    
    SQLite's bm25() function returns negative values where lower (more negative) is better.
    A score of 0.0 indicates no match.
    """
    if score >= 0:
        return 0.0
    val = abs(score)
    # Map [0, inf) to [0, 1) using val / (val + 1.0)
    return val / (val + 1.0)


async def fts_search(
    db: AsyncSession,
    query: str,
    workspace_id: str,
    limit: int = 50,
) -> list[tuple[str, float]]:
    """Perform full-text search on contexts in a workspace using SQLite FTS5 BM25."""
    formatted_query = prepare_fts_query(query)
    if not formatted_query:
        return []

    # SQLite virtual table query using BM25
    # The weights correspond to: title (10.0), content (1.0), context_type (0.0)
    sql = """
        SELECT c.id, bm25(contexts_fts, 10.0, 1.0, 0.0) as score
        FROM contexts c
        JOIN contexts_fts ON contexts_fts.rowid = c.rowid
        WHERE contexts_fts MATCH :query
          AND c.workspace_id = :workspace_id
          AND c.deleted_at IS NULL
        ORDER BY score ASC
        LIMIT :limit
    """
    
    try:
        results = await db.execute(
            text(sql),
            {
                "query": formatted_query,
                "workspace_id": workspace_id,
                "limit": limit,
            }
        )
        return [(row.id, normalize_bm25(row.score)) for row in results]
    except Exception as e:
        logger.error("FTS5 query search failed: %s", str(e), exc_info=True)
        return []
