"""AI Job API router endpoints."""

from __future__ import annotations

import json
import logging
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.jobs.service import AIJobService
from app.features.jobs.schemas import AIJobResponse

logger = logging.getLogger("pocket.features.jobs.router")

router = APIRouter()


@router.get(
    "/{job_id}",
    response_model=AIJobResponse,
    summary="Get background job status and results",
)
async def get_job_status(
    job_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Retrieve details, progress, and results of a background AI job by its ID."""
    service = AIJobService(db)
    job = await service.get_job(job_id)

    results_list = []
    for r in job.results:
        try:
            parsed_data = json.loads(r.result_data)
        except Exception:
            parsed_data = r.result_data

        results_list.append({
            "id": r.id,
            "job_id": r.job_id,
            "result_type": r.result_type,
            "result_data": parsed_data,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "applied": r.applied,
            "created_at": r.created_at,
        })

    return {
        "id": job.id,
        "job_type": job.job_type,
        "status": job.status,
        "progress": job.progress,
        "error_message": job.error_message,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "created_at": job.created_at,
        "results": results_list,
    }
