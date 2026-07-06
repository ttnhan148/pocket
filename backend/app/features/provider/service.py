"""Provider business logic service."""

from __future__ import annotations

import time
from typing import Any
import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.service import BaseService
from app.features.provider.repository import ProviderRepository
from app.features.provider.schemas import ProviderCreate, ProviderUpdate, ProviderTestResponse
from app.features.provider.encryption import encrypt_api_key, decrypt_api_key
from app.models import Provider


class ProviderService(BaseService):
    """Service class handling AI provider configurations."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = ProviderRepository(db)

    async def list_providers(self, skip: int = 0, limit: int = 100) -> list[Provider]:
        """List active/inactive non-deleted providers."""
        return await self.repo.list(skip=skip, limit=limit)

    async def get_provider(self, id_: str) -> Provider:
        """Get provider by ID or raise NotFound."""
        return await self.repo.get_or_raise(id_)

    async def create_provider(self, data: ProviderCreate) -> Provider:
        """Create a new provider configuration with encrypted API key."""
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider with name '{data.name}' already exists",
            )

        encrypted = encrypt_api_key(data.api_key)

        # Check if this is the first provider being created
        existing_list = await self.repo.list(limit=1)
        is_first = len(existing_list) == 0

        provider = Provider(
            name=data.name,
            provider_type=data.provider_type,
            endpoint=data.endpoint,
            api_version=data.api_version,
            deployment_chat=data.deployment_chat,
            deployment_chat_mini=data.deployment_chat_mini,
            deployment_embedding=data.deployment_embedding,
            is_active=data.is_active,
            is_default=1 if is_first else 0,
            api_key_encrypted=encrypted,
        )
        return await self.repo.create(provider)

    async def update_provider(self, id_: str, data: ProviderUpdate) -> Provider:
        """Update provider configuration fields."""
        provider = await self.repo.get_or_raise(id_)

        update_dict: dict[str, Any] = {}
        if data.name is not None:
            if data.name != provider.name:
                existing = await self.repo.get_by_name(data.name)
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Provider with name '{data.name}' already exists",
                    )
            update_dict["name"] = data.name

        if data.provider_type is not None:
            update_dict["provider_type"] = data.provider_type
        if data.endpoint is not None:
            update_dict["endpoint"] = data.endpoint
        if data.api_version is not None:
            update_dict["api_version"] = data.api_version
        if data.deployment_chat is not None:
            update_dict["deployment_chat"] = data.deployment_chat
        if data.deployment_chat_mini is not None:
            update_dict["deployment_chat_mini"] = data.deployment_chat_mini
        if data.deployment_embedding is not None:
            update_dict["deployment_embedding"] = data.deployment_embedding
        if data.is_active is not None:
            update_dict["is_active"] = data.is_active

        if data.api_key is not None:
            update_dict["api_key_encrypted"] = encrypt_api_key(data.api_key)

        return await self.repo.update(id_, update_dict)

    async def set_default_provider(self, id_: str) -> Provider:
        """Set a provider as the default one."""
        provider = await self.repo.get_or_raise(id_)
        if provider.is_active == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot set inactive provider as default",
            )
        updated = await self.repo.set_default(id_)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider {id_} not found",
            )
        return updated

    async def delete_provider(self, id_: str) -> bool:
        """Soft delete a provider, preventing deletion of the default provider."""
        provider = await self.repo.get_or_raise(id_)
        if provider.is_default == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the default provider. Set another provider as default first.",
            )
        return await self.repo.delete(id_, soft=True)

    async def test_connection(self, id_: str) -> ProviderTestResponse:
        """Verify endpoint connectivity and return results."""
        provider = await self.repo.get_or_raise(id_)
        
        api_key = decrypt_api_key(provider.api_key_encrypted or "")
        
        # Determine connection test parameters based on type
        if provider.provider_type in ("openai", "openai_compatible"):
            url = f"{provider.endpoint.rstrip('/')}/models"
            headers = {"Authorization": f"Bearer {api_key}"}
        else:
            # Azure OpenAI
            url = f"{provider.endpoint.rstrip('/')}/openai/deployments?api-version={provider.api_version}"
            headers = {"api-key": api_key}
        
        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(url, headers=headers)
                latency = (time.perf_counter() - start_time) * 1000.0
                
                if res.status_code in (200, 400, 401, 403, 404):
                    # In many cases, it might return 401 (unauthorized) or 404/400 (if endpoint is wrong or deployments empty)
                    # But if the server responds at all, the host endpoint exists.
                    # We consider it a success if we get a structured response (not timeout / network error).
                    # A status of 200 or 400 (e.g. parameter error but connected) is success.
                    # Let's check status specifically:
                    if res.status_code == 200:
                        return ProviderTestResponse(
                            success=True,
                            message="Connection successful! Endpoint resolved and API key accepted.",
                            latency_ms=round(latency, 2),
                        )
                    elif res.status_code in (401, 403):
                        return ProviderTestResponse(
                            success=False,
                            message=f"Authentication failed (HTTP {res.status_code}). Check your API Key.",
                            latency_ms=round(latency, 2),
                        )
                    else:
                        # 404 or 400 means resolved but resource or route not matching. Still reached the server!
                        return ProviderTestResponse(
                            success=True,
                            message=f"Connected to host (HTTP {res.status_code}), but API route or deployment not found.",
                            latency_ms=round(latency, 2),
                        )
                else:
                    return ProviderTestResponse(
                        success=False,
                        message=f"Server returned status code {res.status_code}",
                        latency_ms=round(latency, 2),
                    )
        except httpx.ConnectError:
            return ProviderTestResponse(
                success=False,
                message="Failed to connect. Hostname not resolved or port closed.",
            )
        except httpx.TimeoutException:
            return ProviderTestResponse(
                success=False,
                message="Connection timed out after 5.0 seconds.",
            )
        except Exception as e:
            return ProviderTestResponse(
                success=False,
                message=f"Connection failed: {e!s}",
            )
