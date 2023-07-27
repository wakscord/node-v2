import asyncio
import traceback
from asyncio import AbstractEventLoop
from datetime import timedelta
from signal import SIGINT, SIGTERM

from redis.asyncio import Redis

from app.common.logger import logger
from app.common.process_status import ProcessStatus, process_status_manager
from app.node.constants import NODE_HEALTH_CHECK_INTERVAL, TASK_POP_INTERVAL


class NodeManager:
    _NODE_TASK_QUEUE = "node_task_queue"

    def __init__(self, node_id: str, session: Redis):
        self._node_id = node_id
        self._session = session

    async def join_server(self) -> None:
        await self._ping_session()
        logger.info(f"Start the node server. (node_id: {self._node_id})")

        asyncio.create_task(self._join())
        self._add_signal_handler()

    async def pop_task(self) -> tuple[str, str] | None:
        try:
            return await self._session.blpop(self._NODE_TASK_QUEUE, timeout=TASK_POP_INTERVAL)
        except (TimeoutError, ConnectionError) as exc:
            await self._format_connection_exc(exc)
            return None

    async def _ping_session(self) -> None:
        try:
            await self._session.ping()
        except Exception as exc:
            await self._format_connection_exc(exc)
            exit(0)

    @staticmethod
    async def _format_connection_exc(exc: Exception) -> None:
        logger.warning(f"Connection error. (exception: {exc}), {traceback.format_exc()}")

    async def _join(self) -> None:
        await self._session.hset("node_servers", self._node_id, 1)
        while True:
            await self._health_check()
            await asyncio.sleep(NODE_HEALTH_CHECK_INTERVAL - 1)

    async def _health_check(self) -> None:
        await self._session.setex(
            f"health_check:{self._node_id}", timedelta(seconds=NODE_HEALTH_CHECK_INTERVAL), value=1
        )

    @staticmethod
    def _add_signal_handler() -> None:
        async def _signal_handler(loop: AbstractEventLoop) -> None:
            while True:
                await asyncio.sleep(0.1)
                can_stop = process_status_manager.get_current() == ProcessStatus.WAITING
                if can_stop:
                    try:
                        tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
                        [task.cancel() for task in tasks]
                    finally:
                        await asyncio.sleep(1)
                        loop.stop()

        loop = asyncio.get_running_loop()
        for signal in [SIGINT, SIGTERM]:
            loop.add_signal_handler(signal, lambda x: x.create_task(_signal_handler(x)), loop)
