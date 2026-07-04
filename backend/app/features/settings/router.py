"""Settings API router endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.settings.schemas import SettingBulkUpdateRequest, SettingResponse
from app.features.settings.service import SettingsService

router = APIRouter()


@router.get(
    "",
    response_model=list[SettingResponse],
    summary="Get all global settings",
)
async def list_settings(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[SettingResponse]:
    """Retrieve all global key-value settings."""
    service = SettingsService(db)
    items = await service.get_all_settings()
    return [SettingResponse.model_validate(item) for item in items]


@router.get(
    "/{key}",
    response_model=SettingResponse,
    summary="Get a single setting by key",
)
async def get_setting(
    key: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> SettingResponse:
    """Retrieve a single key-value setting by key."""
    service = SettingsService(db)
    item = await service.get_setting_by_key(key)
    return SettingResponse.model_validate(item)


@router.put(
    "",
    response_model=list[SettingResponse],
    summary="Bulk update settings",
)
async def update_settings(
    body: SettingBulkUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[SettingResponse]:
    """Bulk update multiple settings and validate value type matches."""
    service = SettingsService(db)
    items = await service.update_settings(body.updates)
    return [SettingResponse.model_validate(item) for item in items]
