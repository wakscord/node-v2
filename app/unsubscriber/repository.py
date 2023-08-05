from abc import ABC, abstractmethod

from redis.asyncio import Redis


class UnsubscriberRepository(ABC):
    _UNSUBSCRIBERS_KEY = "unsubscribers"

    @abstractmethod
    async def get_unsubscribers(self) -> set[str]:
        raise NotImplementedError

    @abstractmethod
    async def add_unsubscriber(self, unsubscriber: str) -> None:
        raise NotImplementedError


class UnsubscriberRedisRepository(UnsubscriberRepository):
    def __init__(self, session: Redis):
        self._session = session

    async def get_unsubscribers(self) -> set[str]:
        return await self._session.smembers(self._UNSUBSCRIBERS_KEY)

    async def add_unsubscriber(self, unsubscriber: str) -> None:
        await self._session.sadd(self._UNSUBSCRIBERS_KEY, unsubscriber)
