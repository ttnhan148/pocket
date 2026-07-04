"""Provider API router endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.provider.schemas import (
    ProviderCreate,
    ProviderResponse,
    ProviderUpdate,
    ProviderTestResponse,
)
from app.features.provider.service import ProviderService

router = APIRouter()


@router.get(
    "",
    response_model=list[ProviderResponse],
    summary="List all provider configurations",
)
async def list_providers(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[ProviderResponse]:
    """Retrieve list of all active/inactive provider configurations."""
    service = ProviderService(db)
    items = await service.list_providers()
    return [ProviderResponse.model_validate(item) for item in items]


@router.get(
    "/{id}",
    response_model=ProviderResponse,
    summary="Get provider by ID",
)
async def get_provider(
    id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ProviderResponse:
    """Retrieve details of a single provider configuration."""
    service = ProviderService(db)
    item = await service.get_provider(id)
    return ProviderResponse.model_validate(item)


@router.post(
    "",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new provider configuration",
)
async def create_provider(
    body: ProviderCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ProviderResponse:
    """Create a new AI provider connection settings with encrypted key."""
    service = ProviderService(db)
    item = await service.create_provider(body)
    return ProviderResponse.model_validate(item)


@router.put(
    "/{id}",
    response_model=ProviderResponse,
    summary="Update a provider configuration",
)
async def update_provider(
    id: str,
    body: ProviderUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ProviderResponse:
    """Update fields of an existing provider configuration."""
    service = ProviderService(db)
    item = await service.update_provider(id, body)
    return ProviderResponse.model_validate(item)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a provider configuration",
)
async def delete_provider(
    id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Soft delete a provider configuration (default provider cannot be deleted)."""
    service = ProviderService(db)
    await service.delete_provider(id)
    return None


@router.post(
    "/{id}/default",
    response_model=ProviderResponse,
    summary="Set provider as default",
)
async def set_default_provider(
    id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ProviderResponse:
    """Make this provider configuration the global default."""
    service = ProviderService(db)
    item = await service.set_default_provider(id)
    return ProviderResponse.model_validate(item)


@router.post(
    "/{id}/test",
    response_model=ProviderTestResponse,
    summary="Test provider connection",
)
async def test_provider_connection(
    id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ProviderTestResponse:
    """Ping the endpoint URL with credentials to verify connection success."""
    service = ProviderService(db)
    return await service.test_connection(id)
