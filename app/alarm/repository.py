from abc import ABC, abstractmethod

from redis.asyncio import Redis


class AlarmRepository(ABC):
    _PROXIES_KEY = "proxies"

    @abstractmethod
    async def get_least_usage_proxy(self) -> str | None:
        raise NotImplementedError


class AlarmRedisRepository(AlarmRepository):
    def __init__(self, session: Redis):
        self._session = session

    async def get_least_usage_proxy(self) -> str | None:
        least_usage_proxy: list[str] = await self._session.zrange(self._PROXIES_KEY, start=0, end=0)
        if not least_usage_proxy:
            return None
        proxy = least_usage_proxy[0]
        await self._session.zincrby(self._PROXIES_KEY, 1, proxy)
        return proxy
