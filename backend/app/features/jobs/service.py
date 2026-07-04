"""AI Job Service layer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.service import BaseService
from app.models.ai_job import AIJob, AIJobResult


class AIJobService(BaseService):
    """Business logic for background AI jobs tracking."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def create_job(self, job_type: str, input_data: Dict[str, Any] | None = None) -> AIJob:
        """Create a new pending AI job."""
        input_str = json.dumps(input_data) if input_data else None
        job = AIJob(
            job_type=job_type,
            status="pending",
            input_data=input_str,
            progress=0.0,
        )
        self.db.add(job)
        await self.db.flush()
        return job

    async def start_job(self, job_id: str) -> AIJob:
        """Mark a job as running."""
        stmt = select(AIJob).where(AIJob.id == job_id)
        job = (await self.db.execute(stmt)).scalar_one_or_none()
        if not job:
            raise NotFoundError("AIJob", job_id)

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        await self.db.flush()
        return job

    async def update_progress(
        self,
        job_id: str,
        progress: float,
        status: str = "running",
        error_message: str | None = None,
    ) -> AIJob:
        """Update progress and status of a job."""
        stmt = select(AIJob).where(AIJob.id == job_id)
        job = (await self.db.execute(stmt)).scalar_one_or_none()
        if not job:
            raise NotFoundError("AIJob", job_id)

        job.progress = min(1.0, max(0.0, progress))
        job.status = status
        if error_message:
            job.error_message = error_message

        if status in ["completed", "failed", "cancelled"]:
            job.completed_at = datetime.now(timezone.utc)
            if status == "completed":
                job.progress = 1.0

        await self.db.flush()
        return job

    async def add_result(
        self,
        job_id: str,
        result_type: str,
        result_data: Dict[str, Any],
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> AIJobResult:
        """Add a result object associated with the job."""
        result = AIJobResult(
            job_id=job_id,
            result_type=result_type,
            result_data=json.dumps(result_data),
            entity_type=entity_type,
            entity_id=entity_id,
            applied=0,
        )
        self.db.add(result)
        await self.db.flush()
        return result

    async def get_job(self, job_id: str) -> AIJob:
        """Retrieve job with its results loaded eagerly."""
        stmt = select(AIJob).options(selectinload(AIJob.results)).where(AIJob.id == job_id)
        job = (await self.db.execute(stmt)).scalar_one_or_none()
        if not job:
            raise NotFoundError("AIJob", job_id)
        return job
