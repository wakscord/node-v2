import asyncio
import traceback
from typing import Coroutine

from app.common.logger import logger
from app.retry.constants import RETRY_CHUNK_SIZE, RETRY_TASK_CHECK_INTERVAL


class RetryRateLimiter:
    def __init__(self) -> None:
        self._queue: list[Coroutine] = []

    def add_alarms(self, alarms: list[Coroutine]) -> None:
        self._queue.extend(alarms)

    async def watch_retry(self) -> None:
        asyncio.create_task(self._loop_pop_queue())

    async def _loop_pop_queue(self) -> None:
        while True:
            try:
                if not self._queue:
                    await asyncio.sleep(RETRY_TASK_CHECK_INTERVAL)
                    continue

                alarms = self._queue[:RETRY_CHUNK_SIZE]
                self._queue = self._queue[len(alarms) :]

                await asyncio.gather(*alarms)

            except Exception as exc:
                logger.error(f"Retry 실행 중 에러가 발생했습니다, ({exc})\n{traceback.format_exc()}")
