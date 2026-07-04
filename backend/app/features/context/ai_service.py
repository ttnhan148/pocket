"""AI operations for Contexts (M41)."""

from __future__ import annotations

import logging
from typing import Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.ai.client import AzureAIClient
from app.ai.embeddings import EmbeddingService
from app.ai.pipeline.retrieval import RetrievalEngine
from app.features.context.service import ContextService
from app.features.context.schemas import ContextCreate
from app.features.tags_categories.service import TagService
from app.features.tags_categories.schemas import TagCreate
from app.models import Context

logger = logging.getLogger("pocket.features.context.ai_service")


class AIContextService:
    """Service to handle AI context generation and semantic context suggestions."""

    def __init__(self, db: AsyncSession, ai_client: AzureAIClient, settings: Settings) -> None:
        self.db = db
        self._ai_client = ai_client
        self._settings = settings
        self._context_service = ContextService(db)
        self._tag_service = TagService(db)
        self._embedding_service = EmbeddingService(ai_client, settings)
        self._retrieval_engine = RetrievalEngine(ai_client, self._embedding_service, settings)

    async def generate_context(self, workspace_id: str, description: str) -> Context:
        """Use LLM to generate a structured context from natural language description."""
        if not self._settings.azure_openai_endpoint:
            # Fallback when AI not configured
            data = ContextCreate(
                title=f"AI Generated: {description[:30]}",
                content=f"This is a fallback content generated from: {description}",
                context_type="knowledge",
            )
            return await self._context_service.create_context(workspace_id, data)

        system_prompt = (
            "You are an expert AI system that generates structured context templates for developers.\n"
            "Based on the user's natural language description, generate a structured context.\n"
            "You MUST return a JSON object with the following fields:\n"
            "- title: a concise and descriptive title (maximum 100 characters)\n"
            "- content: the detailed content for the context written in markdown format\n"
            "- context_type: must be one of 'knowledge', 'instruction', or 'persona'\n"
            "- tags: a list of 2-4 lowercase tag names relevant to the content (alphanumeric only)\n"
        )

        try:
            generated = await self._ai_client.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate a context for: {description}"}
                ],
                model=self._settings.azure_openai_deployment_chat_mini,
            )
        except Exception as e:
            logger.error(f"Failed to generate context using AI: {e}")
            raise

        title = generated.get("title", f"AI Generated Context")
        content = generated.get("content", f"Content generated from description: {description}")
        context_type = generated.get("context_type", "knowledge")
        if context_type not in ["knowledge", "instruction", "persona"]:
            context_type = "knowledge"

        # Resolve tags
        tag_ids: List[str] = []
        tags = generated.get("tags", [])
        if isinstance(tags, list):
            for t_name in tags:
                if isinstance(t_name, str) and t_name.strip():
                    try:
                        tag_obj = await self._tag_service.create_tag(
                            TagCreate(name=t_name.strip().lower())
                        )
                        tag_ids.append(tag_obj.id)
                    except Exception as e:
                        logger.warning(f"Failed to create tag {t_name}: {e}")

        # Create context using existing ContextService (handles embedding generation, slugs, FTS, etc.)
        create_payload = ContextCreate(
            title=title,
            content=content,
            context_type=context_type,
            tag_ids=tag_ids,
        )

        return await self._context_service.create_context(workspace_id, create_payload)

    async def suggest_contexts(
        self,
        workspace_id: str,
        draft_content: str,
        already_selected_ids: List[str] | None = None,
        limit: int = 5,
    ) -> List[Context]:
        """Suggest active contexts from workspace that are semantically relevant to draft content."""
        if not draft_content.strip():
            return []

        exclude_ids = set(already_selected_ids or [])

        # Call RetrievalEngine to do a hybrid search
        ranked_items = await self._retrieval_engine.search(
            db=self.db,
            query=draft_content,
            workspace_id=workspace_id,
            top_k=limit + len(exclude_ids),
        )

        # Filter out already selected contexts, deleted contexts, and archived contexts
        suggestions: List[Context] = []
        for item in ranked_items:
            ctx = item.context
            if ctx.id in exclude_ids:
                continue
            if ctx.deleted_at is not None:
                continue
            if ctx.is_archived == 1:
                continue
            suggestions.append(ctx)
            if len(suggestions) >= limit:
                break

        if not suggestions:
            return []

        # Eager load tags for suggestions to prevent MissingGreenlet errors
        from sqlalchemy.orm import selectinload
        ctx_ids = [c.id for c in suggestions]
        stmt = select(Context).options(selectinload(Context.tags)).where(Context.id.in_(ctx_ids))
        res = await self.db.execute(stmt)
        loaded_contexts = {c.id: c for c in res.scalars().all()}

        # Return in the original ranked order
        return [loaded_contexts[c.id] for c in suggestions if c.id in loaded_contexts]
