"""Provider Repository subclassing BaseRepository."""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.models import Provider


class ProviderRepository(BaseRepository[Provider]):
    """Repository class for database access on Provider models."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Provider, db)

    async def get_default(self) -> Provider | None:
        """Fetch the default provider config."""
        stmt = select(Provider).where(
            Provider.is_default == 1,
            Provider.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def set_default(self, provider_id: str) -> Provider | None:
        """Reset is_default on all providers and set the target provider as default."""
        target = await self.get(provider_id)
        if not target:
            return None

        # Reset all other default providers
        reset_stmt = (
            update(Provider)
            .where(Provider.is_default == 1)
            .values(is_default=0)
        )
        await self.db.execute(reset_stmt)

        # Set target as default
        target.is_default = 1
        await self.db.flush()
        return target

    async def get_by_name(self, name: str) -> Provider | None:
        """Fetch provider by unique name."""
        stmt = select(Provider).where(
            Provider.name == name,
            Provider.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()
