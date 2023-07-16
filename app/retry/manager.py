import asyncio
import traceback
from typing import Coroutine

from app.common.logger import logger
from app.retry.constants import RETRY_CHUNK_SIZE


class RetryManager:
    def __init__(self):
        self._queue: list[Coroutine] = []

    async def add(self, task: Coroutine | list[Coroutine]) -> None:
        if isinstance(task, list):
            self._queue.extend(task)
        else:
            self._queue.append(task)

    async def run(self) -> None:
        asyncio.create_task(self.loop())

    async def loop(self) -> None:
        while True:
            try:
                if not self._queue:
                    await asyncio.sleep(0.5)
                    continue

                chunk = self._queue[:RETRY_CHUNK_SIZE]
                self._queue = self._queue[len(chunk) :]

                await asyncio.gather(*chunk)
            except Exception as e:
                logger.error(f"RetryManager 루프 중 오류 발생: {e}\n{traceback.format_exc()}")
