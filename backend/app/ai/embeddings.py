"""Embedding service for generating, saving, and comparing context embeddings."""

from __future__ import annotations

import hashlib
import json
import logging
import math
from datetime import datetime, UTC
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import AzureAIClient
from app.config import Settings
from app.models import Context, ContextEmbedding, AIJob, AIJobResult
from app.models.base import generate_uuid

logger = logging.getLogger("pocket.ai.embeddings")


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two float vectors.
    
    If the vectors are normalized (e.g. from sentence-transformers or Azure OpenAI),
    this is mathematically equivalent to the dot product.
    """
    if len(v1) != len(v2) or not v1:
        return 0.0
    dot_product = sum(x * y for x, y in zip(v1, v2))
    norm_v1 = math.sqrt(sum(x * x for x in v1))
    norm_v2 = math.sqrt(sum(x * x for x in v2))
    if norm_v1 == 0.0 or norm_v2 == 0.0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)


class EmbeddingService:
    """Service to handle embedding generation, local models, similarity, and persistence."""

    def __init__(self, ai_client: AzureAIClient, settings: Settings) -> None:
        self._ai_client = ai_client
        self._settings = settings
        self._local_model: Any = None  # Lazy loaded

    def _get_local_model(self) -> Any:
        """Lazy loads the local sentence-transformers model."""
        if self._local_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading local sentence-transformers model: %s", self._settings.embedding_model_name)
                self._local_model = SentenceTransformer(self._settings.embedding_model_name)
            except Exception as e:
                logger.error("Failed to load local SentenceTransformer: %s", str(e))
                raise RuntimeError(f"Embedding model load failed: {str(e)}") from e
        return self._local_model

    async def embed_text(self, text: str, use_azure: bool = False) -> list[float]:
        """Embed a single text using local model or Azure OpenAI."""
        if use_azure or (self._settings.azure_openai_endpoint and not use_azure and self._settings.embedding_model_name == "azure"):
            # Use Azure OpenAI embedding
            result = await self._ai_client.embed([text])
            return result[0]
        else:
            # Use local sentence-transformers model
            model = self._get_local_model()
            # encode returns numpy array by default, convert to list
            embedding = model.encode(text, normalize_embeddings=True)
            if hasattr(embedding, "tolist"):
                return embedding.tolist()
            return list(embedding)

    async def embed_batch(
        self,
        texts: list[str],
        use_azure: bool = False,
        batch_size: int = 32,
    ) -> list[list[float]]:
        """Embed multiple texts in batches."""
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            if use_azure or (self._settings.azure_openai_endpoint and not use_azure and self._settings.embedding_model_name == "azure"):
                embeddings = await self._ai_client.embed(batch)
            else:
                model = self._get_local_model()
                embeddings_raw = model.encode(
                    batch,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )
                if hasattr(embeddings_raw, "tolist"):
                    embeddings = embeddings_raw.tolist()
                else:
                    embeddings = [list(emb) for emb in embeddings_raw]
            all_embeddings.extend(embeddings)

        return all_embeddings

    async def embed_context(self, db: AsyncSession, context_id: str) -> None:
        """Embed a context if its content changed, and save to database."""
        # Fetch the context
        stmt = select(Context).where(Context.id == context_id, Context.deleted_at.is_(None))
        res = await db.execute(stmt)
        context = res.scalar_one_or_none()
        if not context:
            logger.warning("Attempted to embed non-existent context: %s", context_id)
            return

        content_hash = hashlib.sha256(context.content.encode("utf-8")).hexdigest()
        model_name = self._settings.embedding_model_name

        # Check existing embedding for this context and model
        existing_stmt = select(ContextEmbedding).where(
            ContextEmbedding.context_id == context_id,
            ContextEmbedding.model_name == model_name,
        )
        existing_res = await db.execute(existing_stmt)
        existing = existing_res.scalar_one_or_none()

        if existing:
            if existing.content_hash == content_hash:
                logger.debug("Context embedding unchanged for context: %s", context_id)
                return  # Unchanged, skip
            
            # Content changed, update it
            embedding = await self.embed_text(context.content)
            existing.embedding = json.dumps(embedding)
            existing.dimensions = len(embedding)
            existing.content_hash = content_hash
            existing.updated_at = datetime.now(UTC).isoformat() + "Z"  # type: ignore
            logger.info("Updated existing embedding for context: %s", context_id)
        else:
            # Create new embedding record
            embedding = await self.embed_text(context.content)
            new_embedding = ContextEmbedding(
                id=generate_uuid(),
                context_id=context_id,
                model_name=model_name,
                dimensions=len(embedding),
                embedding=json.dumps(embedding),
                content_hash=content_hash,
            )
            db.add(new_embedding)
            logger.info("Created new embedding for context: %s", context_id)
            
        await db.flush()

    async def schedule_embedding(self, db: AsyncSession, context_id: str) -> str:
        """Schedule a background embedding job by creating a pending AIJob."""
        job = AIJob(
            id=generate_uuid(),
            job_type="embedding",
            status="pending",
            input_data=json.dumps({"context_id": context_id}),
            progress=0.0,
        )
        db.add(job)
        await db.flush()
        logger.info("Scheduled background embedding job: %s for context: %s", job.id, context_id)
        return job.id

    async def run_background_embedding(self, db: AsyncSession, job_id: str) -> None:
        """Executes the scheduled embedding job in the background."""
        stmt = select(AIJob).where(AIJob.id == job_id)
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job or job.status != "pending":
            return

        # Set job status to running
        job.status = "running"
        job.started_at = datetime.now(UTC)
        await db.flush()

        try:
            input_params = json.loads(job.input_data) if job.input_data else {}
            context_id = input_params.get("context_id")
            if not context_id:
                raise ValueError("Job input missing 'context_id'")

            # Perform the embedding
            await self.embed_context(db, context_id)

            # Record success result
            result = AIJobResult(
                id=generate_uuid(),
                job_id=job_id,
                result_type="embedding",
                result_data=json.dumps({"status": "success", "context_id": context_id}),
                entity_type="context",
                entity_id=context_id,
                applied=1,
            )
            db.add(result)

            job.status = "completed"
            job.progress = 1.0
            job.completed_at = datetime.now(UTC)
            await db.commit()
            logger.info("Successfully completed background embedding job: %s", job_id)

        except Exception as e:
            await db.rollback()
            logger.error("Failed executing background embedding job: %s, error: %s", job_id, str(e), exc_info=True)
            
            # Refetch the job to update status on the failed attempt
            res = await db.execute(select(AIJob).where(AIJob.id == job_id))
            failed_job = res.scalar_one_or_none()
            if failed_job:
                failed_job.status = "failed"
                failed_job.error_message = str(e)
                failed_job.completed_at = datetime.now(UTC)
                await db.commit()
