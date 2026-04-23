from abc import ABC, abstractmethod
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository(ABC):
    """Abstract base - any persistence backend must implement these."""

    @abstractmethod
    async def create(self, session: AsyncSession, entity: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, session: AsyncSession, entity_id: UUID) -> Optional[Any]:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, session: AsyncSession, **filters) -> list[Any]:
        raise NotImplementedError
