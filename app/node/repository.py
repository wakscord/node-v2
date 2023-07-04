import asyncio
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any

from redis.asyncio import Redis

from app.common.settings import settings
from app.node.constants import NODE_HEALTH_CHECK_INTERVAL


class NodeRepository(ABC):
    @abstractmethod
    def __init__(self, session: Any):
        self._session = session

    @abstractmethod
    async def join(self) -> None:
        raise NotImplemented

    @abstractmethod
    async def _health_check(self) -> None:
        raise NotImplemented


class NodeRedisRepository(NodeRepository):
    def __init__(self, session: Redis):
        self._session = session

    async def join(self) -> None:
        await self._session.hset("node_servers", settings.NODE_ID, 1)
        while True:
            await self._health_check()
            await asyncio.sleep(NODE_HEALTH_CHECK_INTERVAL - 1)

    async def _health_check(self) -> None:
        await self._session.setex(
            f"health_check-{settings.NODE_ID}", timedelta(seconds=NODE_HEALTH_CHECK_INTERVAL), value=1
        )
