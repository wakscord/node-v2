from abc import ABC, abstractmethod
from typing import Any

from redis.asyncio import Redis


class AlarmRepository(ABC):
    _PROXIES_KEY = "proxies"
    _UNSUBSCRIBERS_KEY = "unsubscribers"

    @abstractmethod
    def __init__(self, session: Any):
        self._session = session

    @abstractmethod
    async def get_unsubscribers(self) -> set[str]:
        raise NotImplementedError

    @abstractmethod
    async def add_unsubscriber(self, unsubscriber: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_least_usage_proxy(self) -> set[str]:
        raise NotImplementedError


class AlarmRedisRepository(AlarmRepository):
    def __init__(self, session: Redis):
        self._session = session

    async def get_unsubscribers(self) -> set[str]:
        return await self._session.smembers(self._UNSUBSCRIBERS_KEY)

    async def add_unsubscriber(self, unsubscriber: str) -> None:
        await self._session.sadd(self._UNSUBSCRIBERS_KEY, unsubscriber)

    async def get_least_usage_proxy(self) -> str | None:
        least_usage_proxy: list[str] = await self._session.zrange(self._PROXIES_KEY, start=0, end=0)
        if not least_usage_proxy:
            return None
        proxy = least_usage_proxy[0]
        await self._session.zincrby(self._PROXIES_KEY, 1, proxy)
        return proxy
