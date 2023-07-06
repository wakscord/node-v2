from abc import ABC, abstractmethod
from typing import Any

from redis.asyncio import Redis


class AlarmRepository(ABC):
    UNSUBSCRIBERS_KEY = "unsubscribers"

    @abstractmethod
    def __init__(self, session: Any):
        self._session = session

    @abstractmethod
    async def get_unsubscribers(self) -> set[str]:
        raise NotImplementedError

    @abstractmethod
    async def add_unsubscriber(self, unsubscriber: str) -> None:
        raise NotImplementedError


class AlarmRedisRepository(AlarmRepository):
    def __init__(self, session: Redis):
        self._session = session

    async def get_unsubscribers(self) -> set[str]:
        return await self._session.smembers(self.UNSUBSCRIBERS_KEY)

    async def add_unsubscriber(self, unsubscriber: str) -> None:
        await self._session.sadd(self.UNSUBSCRIBERS_KEY, unsubscriber)
