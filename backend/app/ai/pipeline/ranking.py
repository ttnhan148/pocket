"""Multi-factor context ranking algorithm implementing 9-factor scoring."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any

from app.ai.pipeline.retrieval import RetrievalResult
from app.models import Context

logger = logging.getLogger("pocket.ai.pipeline.ranking")


@dataclass
class RankedContext:
    """Represents a ranked context containing the score breakdown for explaining results."""
    context: Context
    score: float
    score_breakdown: dict[str, float]


class RankingEngine:
    """Calculates final scores for retrieved contexts using a 9-factor weight matrix."""

    RANKING_WEIGHTS = {
        "semantic": 0.25,     # Semantic similarity/score from retrieval
        "priority": 0.15,     # User priority (0-100 -> 0.0 - 1.0)
        "usage": 0.10,        # Usage count (log-normalized)
        "recency": 0.10,      # Decay function on days since last use
        "workspace": 0.05,    # Boost if matching target workspace (1.0 vs 0.3)
        "favorite": 0.05,     # Boost if favorited (1.0 vs 0.0)
        "dependency": 0.10,   # Weight from incoming dependency count
        "confidence": 0.10,   # Context confidence score (0.0 - 1.0)
        "quality": 0.10,      # Context quality score (0.0 - 1.0)
    }

    def _usage_score(self, count: int) -> float:
        """Log-normalized usage score with diminishing returns."""
        if count <= 0:
            return 0.0
        return min(1.0, math.log(count + 1) / math.log(100))

    def _recency_score(self, last_used_at: str | None) -> float:
        """Exponential decay based on days since last use (half-life of ~14 days)."""
        if not last_used_at:
            return 0.0
        try:
            last_used = datetime.fromisoformat(last_used_at.replace("Z", "+00:00"))
            days = (datetime.now(UTC) - last_used).days
            return math.exp(-0.05 * max(0, days))
        except Exception:
            return 0.5

    def rank(
        self,
        results: list[RetrievalResult],
        workspace_id: str,
        favorites: set[str],
        dependency_weights: dict[str, float] | None = None,
    ) -> list[RankedContext]:
        """Calculates final scores and sorts contexts based on the 9-factor formula."""
        ranked_contexts: list[RankedContext] = []
        dep_weights = dependency_weights or {}

        for res in results:
            ctx = res.context
            
            # Compute individual score factors (normalized 0.0 - 1.0)
            scores = {
                "semantic": res.final_score,
                "priority": ctx.priority / 100.0,
                "usage": self._usage_score(ctx.usage_count),
                "recency": self._recency_score(ctx.last_used_at),
                "workspace": 1.0 if ctx.workspace_id == workspace_id else 0.3,
                "favorite": 1.0 if ctx.id in favorites else 0.0,
                "dependency": dep_weights.get(ctx.id, 0.0),
                "confidence": ctx.confidence,
                "quality": ctx.quality_score if ctx.quality_score is not None else 0.5,
            }

            # Calculate weighted sum
            final_score = sum(
                self.RANKING_WEIGHTS[factor] * score_val
                for factor, score_val in scores.items()
            )

            ranked_contexts.append(
                RankedContext(
                    context=ctx,
                    score=final_score,
                    score_breakdown=scores,
                )
            )

        # Sort descending by final score
        ranked_contexts.sort(key=lambda x: x.score, reverse=True)
        return ranked_contexts
