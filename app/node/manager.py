import asyncio
from datetime import timedelta

from redis import Redis

from app.common.logger import logger
from app.node.constants import NODE_HEALTH_CHECK_INTERVAL


class NodeManager:
    def __init__(self, node_id: str, session: Redis):
        self._node_id = node_id
        self._session = session

    async def join_server(self) -> None:
        await self._ping_session()

        logger.info(f"Start the node server. (node_id: {self._node_id})")
        asyncio.create_task(self._join())

    async def _ping_session(self):
        try:
            await self._session.ping()
        except Exception as exc:
            logger.warning(f"Redis connection error. (exception: {exc})")
            exit(0)

    async def _join(self) -> None:
        await self._session.hset("node_servers", self._node_id, 1)
        while True:
            await self._health_check()
            await asyncio.sleep(NODE_HEALTH_CHECK_INTERVAL - 1)

    async def _health_check(self) -> None:
        await self._session.setex(
            f"health_check:{self._node_id}", timedelta(seconds=NODE_HEALTH_CHECK_INTERVAL), value=1
        )