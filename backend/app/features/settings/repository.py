"""Setting Repository for database access on Setting models."""

from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Setting
from app.features.settings.schemas import SettingUpdate


class SettingRepository:
    """Repository class for Settings (non-UUID keys)."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_all(self) -> list[Setting]:
        """Fetch all settings ordered by category and key."""
        stmt = select(Setting).order_by(Setting.category, Setting.key)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_by_key(self, key: str) -> Setting | None:
        """Fetch a setting by its unique string key."""
        stmt = select(Setting).where(Setting.key == key)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def bulk_update(self, updates: list[SettingUpdate]) -> list[Setting]:
        """Bulk update settings by key."""
        keys = [u.key for u in updates]
        stmt = select(Setting).where(Setting.key.in_(keys))
        res = await self.db.execute(stmt)
        settings_map = {s.key: s for s in res.scalars().all()}

        updated: list[Setting] = []
        for u in updates:
            if u.key in settings_map:
                setting = settings_map[u.key]
                setting.value = u.value
                updated.append(setting)

        await self.db.flush()
        return updated
