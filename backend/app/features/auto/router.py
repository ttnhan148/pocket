"""APIs for AI-powered Auto Tagging, Variable Extraction, and Duplicate Merges."""

from __future__ import annotations

from typing import Annotated, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.config import Settings
from app.ai.client import AzureAIClient
from app.features.auto.tagging_service import AutoTaggingService
from app.features.auto.dedup_service import DedupService
from app.features.context.schemas import ContextResponse

router = APIRouter()


class TagRequest(BaseModel):
    content: str


class TagResponse(BaseModel):
    tags: List[str]


class VariableExtractRequest(BaseModel):
    content: str


class VariableExtractionDetail(BaseModel):
    name: str
    suggested_value: str
    confidence: float


class VariableExtractResponse(BaseModel):
    variables: List[VariableExtractionDetail]


class DuplicateScanResult(BaseModel):
    context_a: Dict[str, str]
    context_b: Dict[str, str]
    similarity: float


class MergeRequest(BaseModel):
    context_ids: List[str]
    target_title: str


@router.post("/tag", response_model=TagResponse, summary="Suggest tags for context text")
async def suggest_tags(data: TagRequest) -> TagResponse:
    settings = Settings()
    ai_client = AzureAIClient(settings)
    service = AutoTaggingService(ai_client, settings)
    tags = await service.suggest_tags(data.content)
    return TagResponse(tags=tags)


@router.post("/extract-variables", response_model=VariableExtractResponse, summary="Extract variables from template content")
async def extract_variables(data: VariableExtractRequest) -> VariableExtractResponse:
    settings = Settings()
    ai_client = AzureAIClient(settings)
    service = AutoTaggingService(ai_client, settings)
    vars_ = await service.extract_variables(data.content)
    return VariableExtractResponse(variables=vars_)


@router.get("/duplicates", response_model=List[DuplicateScanResult], summary="Scan workspace for duplicate contexts")
async def scan_duplicates(
    workspace_id: str,
    threshold: float = 0.90,
    db: Annotated[AsyncSession, Depends(get_session)] = None,
) -> List[DuplicateScanResult]:
    settings = Settings()
    ai_client = AzureAIClient(settings)
    service = DedupService(db, ai_client, settings)
    duplicates = await service.scan_duplicates(workspace_id, threshold)
    return [DuplicateScanResult.model_validate(d) for d in duplicates]


@router.post("/merge", response_model=ContextResponse, summary="Consolidate duplicate contexts into a new context")
async def merge_contexts(
    data: MergeRequest,
    db: Annotated[AsyncSession, Depends(get_session)] = None,
) -> ContextResponse:
    settings = Settings()
    ai_client = AzureAIClient(settings)
    service = DedupService(db, ai_client, settings)
    merged = await service.merge_contexts(data.context_ids, data.target_title)
    return ContextResponse.model_validate(merged)
