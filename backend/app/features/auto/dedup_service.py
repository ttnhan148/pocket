"""AI-powered duplicate detection and context merging service."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.exceptions import NotFoundError, ValidationError
from app.ai.client import AzureAIClient
from app.ai.embeddings import cosine_similarity
from app.models import Context, ContextDependency, ContextEmbedding

logger = logging.getLogger("pocket.features.auto.dedup")

MERGE_PROMPT = """You are an editor. Consolidate and merge the following duplicated context blocks into a single, cohesive, high-quality, comprehensive markdown text. Remove redundant statements while preserving all technical details, rules, and instruction sets.
Return JSON format strictly:
{
  "merged_content": "..."
}
"""


class DedupService:
    """Detects near-duplicate contexts in a workspace and offers AI merges."""

    def __init__(self, db: AsyncSession, ai_client: AzureAIClient, settings: Settings) -> None:
        self.db = db
        self._ai_client = ai_client
        self._settings = settings

    async def scan_duplicates(self, workspace_id: str, threshold: float = 0.90) -> List[Dict[str, Any]]:
        """Identify context pairs with embedding similarity higher than the threshold."""
        # 1. Fetch active contexts
        stmt_ctx = select(Context).where(
            Context.workspace_id == workspace_id,
            Context.deleted_at.is_(None),
            Context.is_archived == 0,
        )
        res_ctx = await self.db.execute(stmt_ctx)
        contexts = list(res_ctx.scalars().all())

        if len(contexts) < 2:
            return []

        # 2. Fetch embeddings
        ctx_ids = [c.id for c in contexts]
        stmt_emb = select(ContextEmbedding).where(ContextEmbedding.context_id.in_(ctx_ids))
        res_emb = await self.db.execute(stmt_emb)
        embeddings = {e.context_id: json.loads(e.embedding) for e in res_emb.scalars().all()}

        duplicates: List[Dict[str, Any]] = []
        seen_pairs: Set[str] = set()

        # 3. Compare all pairs
        for i, c1 in enumerate(contexts):
            emb1 = embeddings.get(c1.id)
            if not emb1:
                continue
            for j, c2 in enumerate(contexts[i+1:]):
                emb2 = embeddings.get(c2.id)
                if not emb2:
                    continue
                
                similarity = cosine_similarity(emb1, emb2)
                if similarity >= threshold:
                    pair_key = "-".join(sorted([c1.id, c2.id]))
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        duplicates.append({
                            "context_a": {
                                "id": c1.id,
                                "title": c1.title,
                                "context_type": c1.context_type,
                            },
                            "context_b": {
                                "id": c2.id,
                                "title": c2.title,
                                "context_type": c2.context_type,
                            },
                            "similarity": float(similarity),
                        })

        return duplicates

    async def merge_contexts(self, context_ids: List[str], target_title: str) -> Context:
        """Call AI to consolidate duplicate contexts, create new merged context, map dependencies, and archive old ones."""
        if not context_ids:
            raise ValidationError("Must provide at least one context to merge")

        # 1. Fetch contexts
        stmt = select(Context).where(Context.id.in_(context_ids), Context.deleted_at.is_(None))
        res = await self.db.execute(stmt)
        contexts = list(res.scalars().all())

        if len(contexts) != len(context_ids):
            raise NotFoundError("Context", f"One or more context IDs in {context_ids} not found")

        workspace_id = contexts[0].workspace_id
        context_type = contexts[0].context_type

        # 2. Call AI to merge contents
        merged_content = "\n\n".join(c.content for c in contexts)
        if self._settings.azure_openai_endpoint:
            try:
                ai_res = await self._ai_client.chat_json(
                    messages=[
                        {"role": "system", "content": MERGE_PROMPT},
                        {"role": "user", "content": json.dumps([
                            {"title": c.title, "content": c.content}
                            for c in contexts
                        ])},
                    ],
                    model=self._settings.azure_openai_deployment_chat,
                    temperature=0.3,
                )
                merged_content = ai_res.get("merged_content", merged_content)
            except Exception as e:
                logger.warning("AI context merging failed, falling back to concatenation: %s", str(e))

        # 3. Create new merged Context
        from slugify import slugify
        base_slug = slugify(target_title)
        slug = base_slug
        counter = 2
        
        # Check slug unique constraint
        while True:
            exist_stmt = select(Context).where(
                Context.workspace_id == workspace_id,
                Context.slug == slug,
                Context.deleted_at.is_(None),
            )
            exist_res = await self.db.execute(exist_stmt)
            if not exist_res.scalar_one_or_none():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1

        merged_context = Context(
            workspace_id=workspace_id,
            title=target_title,
            slug=slug,
            content=merged_content,
            context_type=context_type,
            priority=max(c.priority for c in contexts),
            confidence=sum(c.confidence for c in contexts) / len(contexts),
        )
        self.db.add(merged_context)
        await self.db.flush()

        # 4. Re-map Dependency edges
        # Edges where old contexts are targets (dependencies) should now point to new context
        stmt_edges_dep = select(ContextDependency).where(
            ContextDependency.target_id.in_(context_ids),
            ContextDependency.deleted_at.is_(None)
        )
        res_edges_dep = await self.db.execute(stmt_edges_dep)
        for edge in res_edges_dep.scalars().all():
            edge.target_id = merged_context.id

        # Edges where old contexts are sources (dependents) should now point from new context
        stmt_edges_src = select(ContextDependency).where(
            ContextDependency.source_id.in_(context_ids),
            ContextDependency.deleted_at.is_(None)
        )
        res_edges_src = await self.db.execute(stmt_edges_src)
        for edge in res_edges_src.scalars().all():
            edge.source_id = merged_context.id

        # 5. Archive old contexts
        now = datetime.now(timezone.utc)
        for c in contexts:
            c.is_archived = 1
            c.deleted_at = now

        await self.db.flush()
        
        # Refresh to eager load tags
        from sqlalchemy.orm import selectinload
        refreshed_stmt = select(Context).options(selectinload(Context.tags)).where(Context.id == merged_context.id)
        refreshed_res = await self.db.execute(refreshed_stmt)
        return refreshed_res.scalar_one()
