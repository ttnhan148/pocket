"""Hybrid retrieval engine combining FTS5, RapidFuzz, and Semantic search."""

from __future__ import annotations

import asyncio
import json
import logging
import math
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import AzureAIClient
from app.ai.embeddings import EmbeddingService, cosine_similarity
from app.ai.pipeline.fuzzy import fuzzy_search
from app.ai.pipeline.search import fts_search
from app.config import Settings
from app.models import Context, ContextEmbedding

logger = logging.getLogger("pocket.ai.pipeline.retrieval")


@dataclass
class RetrievalResult:
    """Represents a retrieved context with method-specific scores and merged score."""
    context: Context
    fts_score: float        # FTS5 score (0.0 - 1.0)
    fuzzy_score: float      # RapidFuzz score (0.0 - 1.0)
    semantic_score: float   # Cosine similarity (0.0 - 1.0)
    metadata_score: float   # Metadata score (0.0 - 1.0)
    final_score: float      # Weighted final score (0.0 - 1.0)


class RetrievalEngine:
    """Combines text search, fuzzy match, and semantic embeddings into a hybrid search result."""

    # Configured weights for hybrid retrieval
    WEIGHTS = {
        "fts": 0.25,
        "fuzzy": 0.10,
        "semantic": 0.35,
        "metadata": 0.30,
    }

    def __init__(
        self,
        ai_client: AzureAIClient,
        embedding_service: EmbeddingService,
        settings: Settings,
    ) -> None:
        self._ai_client = ai_client
        self._embedding_service = embedding_service
        self._settings = settings

    async def _rewrite_query(self, query: str, intent: Any | None) -> str:
        """Expands/rewrites the user query for higher recall if necessary."""
        expanded = query
        # 1. Simple expansion: append intent entities if present
        if intent and hasattr(intent, "entities") and intent.entities:
            expanded = f"{query} {' '.join(intent.entities)}"

        # 2. For complex intent/queries, prompt AI to produce search terms
        if intent and hasattr(intent, "complexity") and intent.complexity == "complex" and self._settings.azure_openai_endpoint:
            try:
                system_prompt = (
                    "You are a query expansion assistant. Generate an expanded, space-separated string "
                    "of search keywords, synonyms, or related concepts based on the user's query to improve search recall. "
                    "Format the response strictly as a JSON object: {\"expanded_query\": \"...\"}"
                )
                result = await self._ai_client.chat_json(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query},
                    ],
                    model=self._settings.azure_openai_deployment_chat_mini,
                    temperature=0.1,
                )
                expanded = result.get("expanded_query", expanded)
            except Exception as e:
                logger.warning("Query rewrite step failed, falling back to basic expansion: %s", str(e))
                
        return expanded

    async def _semantic_search(
        self,
        db: AsyncSession,
        query: str,
        workspace_id: str,
        limit: int = 50,
        min_threshold: float = 0.3,
    ) -> list[tuple[str, float]]:
        """Compute query embedding and calculate cosine similarity against all active contexts in workspace."""
        try:
            # Compute query embedding
            query_embedding = await self._embedding_service.embed_text(query)
            
            # Fetch all stored context embeddings for this workspace
            stmt = (
                select(ContextEmbedding)
                .join(Context, Context.id == ContextEmbedding.context_id)
                .where(
                    Context.workspace_id == workspace_id,
                    Context.deleted_at.is_(None),
                    ContextEmbedding.model_name == self._settings.embedding_model_name,
                )
            )
            res = await db.execute(stmt)
            db_embeddings = res.scalars().all()
            
            scores: list[tuple[str, float]] = []
            for db_emb in db_embeddings:
                try:
                    vector = json.loads(db_emb.embedding)
                    sim = cosine_similarity(query_embedding, vector)
                    if sim >= min_threshold:
                        scores.append((db_emb.context_id, sim))
                except Exception as parse_err:
                    logger.error("Failed to parse vector embedding for context %s: %s", db_emb.context_id, str(parse_err))
                    
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[:limit]
        except Exception as e:
            logger.error("Semantic search step failed: %s", str(e), exc_info=True)
            return []

    def _compute_metadata_score(self, context: Context) -> float:
        """Calculate a metadata score from priority, usage frequency, and recency."""
        # 1. Normalized priority (0-100 -> 0-1)
        priority_score = context.priority / 100.0
        
        # 2. Log-normalized usage
        count = context.usage_count
        usage_score = min(1.0, math.log(count + 1) / math.log(100)) if count > 0 else 0.0
        
        # 3. Recency score with exponential decay (half-life of ~14 days)
        recency_score = 0.5
        if context.last_used_at:
            try:
                last_used = datetime.fromisoformat(context.last_used_at.replace("Z", "+00:00"))
                days = (datetime.now(UTC) - last_used).days
                recency_score = math.exp(-0.05 * max(0, days))
            except Exception:
                recency_score = 0.5
                
        # Merge factors: priority (40%), usage (30%), recency (30%)
        return 0.4 * priority_score + 0.3 * usage_score + 0.3 * recency_score

    async def search(
        self,
        db: AsyncSession,
        query: str,
        workspace_id: str,
        intent: Any | None = None,
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        """Perform hybrid retrieval combining FTS, Fuzzy, and Semantic search with metadata boost."""
        if not query.strip():
            return []

        # Step 1: Query expansion
        expanded_query = await self._rewrite_query(query, intent)

        # Step 2: Parallel search execution
        fts_task = fts_search(db, expanded_query, workspace_id, limit=50)
        fuzzy_task = fuzzy_search(db, query, workspace_id, limit=50)
        semantic_task = self._semantic_search(db, query, workspace_id, limit=50)
        
        fts_res, fuzzy_res, semantic_res = await asyncio.gather(fts_task, fuzzy_task, semantic_task)

        # Step 3: Merge result IDs
        # Gather all unique context IDs
        all_ids = set([r[0] for r in fts_res] + [r[0] for r in fuzzy_res] + [r[0] for r in semantic_res])
        if not all_ids:
            return []

        # Load context objects from database
        context_stmt = select(Context).where(Context.id.in_(all_ids), Context.deleted_at.is_(None))
        contexts_db = (await db.execute(context_stmt)).scalars().all()
        context_map = {c.id: c for c in contexts_db}

        # Convert result lists to dicts for fast lookup
        fts_map = dict(fts_res)
        fuzzy_map = dict(fuzzy_res)
        semantic_map = dict(semantic_res)

        retrieval_results = []
        for ctx_id in all_ids:
            context = context_map.get(ctx_id)
            if not context:
                continue

            fts_val = fts_map.get(ctx_id, 0.0)
            fuzzy_val = fuzzy_map.get(ctx_id, 0.0)
            semantic_val = semantic_map.get(ctx_id, 0.0)
            metadata_val = self._compute_metadata_score(context)

            # Compute weighted merge
            final_score = (
                self.WEIGHTS["fts"] * fts_val +
                self.WEIGHTS["fuzzy"] * fuzzy_val +
                self.WEIGHTS["semantic"] * semantic_val +
                self.WEIGHTS["metadata"] * metadata_val
            )

            retrieval_results.append(
                RetrievalResult(
                    context=context,
                    fts_score=fts_val,
                    fuzzy_score=fuzzy_val,
                    semantic_score=semantic_val,
                    metadata_score=metadata_val,
                    final_score=final_score,
                )
            )

        # Sort descending by final score
        retrieval_results.sort(key=lambda r: r.final_score, reverse=True)
        return retrieval_results[:top_k]
