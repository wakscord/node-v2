from abc import ABC, abstractmethod
from typing import Any

from redis import Redis


class AlarmRepository(ABC):
    UNSUBSCRIBERS_KEY = "unsubscribers"

    @abstractmethod
    def __init__(self, session: Any):
        self._session = session

    @abstractmethod
    async def get_unsubscribers(self) -> set[str]:
        raise NotImplemented

    @abstractmethod
    async def add_unsubscriber(self, unsubscriber: str) -> None:
        raise NotImplemented


class AlarmRedisRepository(AlarmRepository):
    def __init__(self, session: Redis):
        self._session = session

    async def get_unsubscribers(self) -> set[str]:
        unsubscribers = await self._session.smembers(self.UNSUBSCRIBERS_KEY)
        return {unsubscriber.decode("utf-8") for unsubscriber in unsubscribers}

    async def add_unsubscriber(self, unsubscriber: str) -> None:
        await self._session.sadd(self.UNSUBSCRIBERS_KEY, unsubscriber)
