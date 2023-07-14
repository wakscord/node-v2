import asyncio
import math
import traceback
from typing import Callable

import aiohttp
import orjson
from aiohttp import BasicAuth, ClientResponse, ClientSession

from app.alarm.constants import DEFAULT_RETRY_AFTER, DISCORD_WEBHOOK_URL
from app.alarm.exceptions import AlarmSendFailedException, RateLimitException
from app.alarm.repository import AlarmRedisRepository
from app.alarm.response_validator import AlarmResponseValidator
from app.common.logger import logger
from app.common.settings import settings


class AlarmSender:
    def __init__(self, repo: AlarmRedisRepository):
        self._repo = repo

    async def send(self, subscribers: list[str], message: dict) -> None:
        unsubscribers: set[str] = await self._repo.get_unsubscribers()
        active_subscribers = self._exclude_unsubscribers(subscribers, unsubscribers)
        await self._send(active_subscribers, message)

    async def _send(self, subscribers: set[str], message: dict) -> None:
        headers = {"Content-Type": "application/json"}
        data = orjson.dumps(message)

        chunked_subscribers_list = self._chunk_subscribers(list(subscribers), settings.MAX_CONCURRENT)
        for chunked_subscribers in chunked_subscribers_list:
            async with aiohttp.ClientSession(headers=headers) as session:
                tasks = [
                    self._request(session, url=f"{DISCORD_WEBHOOK_URL}{key}", data=data) for key in chunked_subscribers
                ]
                await asyncio.gather(*tasks)

    async def _request(self, session: ClientSession, url: str, data: bytes, retry_attempt: int = 10) -> None:
        retry_after = DEFAULT_RETRY_AFTER
        proxy = await self._repo.get_least_usage_proxy()
        proxy_auth = BasicAuth(settings.PROXY_USER, settings.PROXY_PASSWORD) if proxy else None

        for idx in range(retry_attempt):
            try:
                await asyncio.sleep(retry_after * idx)
                response: ClientResponse = await session.post(url=url, data=data, proxy=proxy, proxy_auth=proxy_auth)
                if await AlarmResponseValidator(self._repo).is_done(response):
                    break
            except RateLimitException as exc:
                retry_after = exc.retry_after
            except AlarmSendFailedException as exc:
                logger.warning(exc)
            except aiohttp.ClientConnectionError as exc:
                logger.warning(f"클라이언트 커넥션 에러가 발생했습니다, (exception: {exc})")
            except Exception as exc:
                traceback.print_exc()
                logger.warning(f"전송에 실패했습니다, (exception: {exc})")

    @staticmethod
    def _exclude_unsubscribers(subscribers: list[str], unsubscribers: set[str]) -> set[str]:
        return set(subscribers) - unsubscribers

    @staticmethod
    def _chunk_subscribers(subscribers: list[str], max_concurrent: int) -> list[list[str]]:
        chunk_len: int = math.ceil(len(subscribers) / max_concurrent)
        start_idx: Callable[[int], int] = lambda current_idx: current_idx * max_concurrent
        # fmt: off
        return [subscribers[start_idx(idx): start_idx(idx) + max_concurrent] for idx in range(0, chunk_len)]
