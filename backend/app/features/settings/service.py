"""Settings business logic service."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.service import BaseService
from app.features.settings.repository import SettingRepository
from app.features.settings.schemas import SettingUpdate
from app.models import Setting


class SettingsService(BaseService):
    """Service class handling settings updates and retrieval."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = SettingRepository(db)

    async def get_all_settings(self) -> list[Setting]:
        """Get all application settings."""
        return await self.repo.list_all()

    async def get_setting_by_key(self, key: str) -> Setting:
        """Get setting by key or raise 404."""
        setting = await self.repo.get_by_key(key)
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting with key '{key}' not found",
            )
        return setting

    async def update_settings(self, updates: list[SettingUpdate]) -> list[Setting]:
        """Validate and bulk update settings."""
        # Pre-load settings for validation
        for update in updates:
            setting = await self.repo.get_by_key(update.key)
            if not setting:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Setting with key '{update.key}' not found",
                )

            # Validate type compatibility
            val_type = setting.value_type.lower()
            val_str = update.value.strip().lower()

            if val_type == "boolean":
                if val_str not in ("true", "false", "1", "0"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Setting '{update.key}' expects a boolean value (true/false).",
                    )
            elif val_type == "number":
                try:
                    # Validate that it can be parsed as float or int
                    if "." in update.value:
                        float(update.value)
                    else:
                        int(update.value)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Setting '{update.key}' expects a numeric value.",
                    )

        # Update and save
        return await self.repo.bulk_update(updates)
