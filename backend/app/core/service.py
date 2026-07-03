"""Base Service class."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


class BaseService:
    """Base service encapsulating transactional business logic and database sessions."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
