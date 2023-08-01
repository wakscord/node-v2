import asyncio
import math
import traceback
from typing import Callable

import aiohttp
from aiohttp import BasicAuth, ClientResponse, ClientSession

from app.alarm.constants import DEFAULT_RETRY_AFTER, DEFAULT_RETRY_ATTEMPT, DISCORD_WEBHOOK_URL
from app.alarm.dtos import SendResponseDTO
from app.alarm.exceptions import AlarmSendFailedException, RateLimitException, UnsubscriberException
from app.alarm.repository import AlarmRepository
from app.alarm.response_validator import AlarmResponseValidator
from app.common.logger import logger
from app.common.settings import settings
from app.retry.rate_limiter import RetryRateLimiter
from app.unsubscriber.repository import UnsubscriberRepository


class AlarmService:
    _headers = {"Content-Type": "application/json"}

    def __init__(
        self,
        alarm_repo: AlarmRepository,
        unsubscriber_repo: UnsubscriberRepository,
        retry_rate_limiter: RetryRateLimiter,
    ):
        self._alarm_repo = alarm_repo
        self._unsubscriber_repo = unsubscriber_repo
        self.retry_rate_limiter = retry_rate_limiter

    async def send(self, subscribers: list[str], message: bytes) -> None:
        chunked_subscribers_list = self._chunk_subscribers(subscribers, settings.MAX_CONCURRENT)
        for chunked_subscribers in chunked_subscribers_list:
            failed_subscribers: list[str] = await self._send(chunked_subscribers, message)
            if not failed_subscribers:
                continue
            await self._retry_send(failed_subscribers, message)

    async def _send(self, subscribers: list[str], message: bytes) -> list[str]:
        proxy = await self._alarm_repo.get_least_usage_proxy()
        async with aiohttp.ClientSession(headers=self._headers) as session:
            alarms = [
                self._request(session, url=f"{DISCORD_WEBHOOK_URL}{key}", data=message, proxy=proxy)
                for key in subscribers
            ]
            responses = await asyncio.gather(*alarms)
            return [response for response in responses if response]

    async def _request(self, session: ClientSession, url: str, data: bytes, proxy: str | None) -> str | None:
        proxy_auth = BasicAuth(settings.PROXY_USER, settings.PROXY_PASSWORD) if proxy else None
        try:
            response: ClientResponse = await session.post(url=url, data=data, proxy=proxy, proxy_auth=proxy_auth)
            response_dto = SendResponseDTO(url=response.url, status=response.status, text=response.text)
            await AlarmResponseValidator.validate(response_dto)
            return None
        except UnsubscriberException as exc:
            if exc.unsubscriber:
                await self._unsubscriber_repo.add_unsubscriber(exc.unsubscriber)
        except (RateLimitException, AlarmSendFailedException) as exc:
            logger.warning(exc)
        except aiohttp.ClientConnectionError as exc:
            logger.warning(f"클라이언트 커넥션 에러가 발생했습니다, (exception: {exc})")
        except Exception as exc:
            logger.warning(f"전송에 실패했습니다, (exception: {exc}\n{traceback.format_exc()})")
        return url

    async def _retry_send(self, failed_subscribers: list[str], message: bytes) -> None:
        proxy = await self._alarm_repo.get_least_usage_proxy()
        retry_alarms = [self._retry(url=subscriber, message=message, proxy=proxy) for subscriber in failed_subscribers]
        self.retry_rate_limiter.add_alarms(retry_alarms)

    async def _retry(self, url: str, message: bytes, proxy: str | None) -> None:
        remain_retry_attempt = DEFAULT_RETRY_ATTEMPT
        async with aiohttp.ClientSession(headers=self._headers) as session:
            while True:
                is_success = not await self._request(session, url=url, data=message, proxy=proxy)
                if is_success or not remain_retry_attempt:
                    break
                remain_retry_attempt -= 1
                current_retry_attempt = DEFAULT_RETRY_ATTEMPT - remain_retry_attempt
                await asyncio.sleep(current_retry_attempt * DEFAULT_RETRY_AFTER)

    @staticmethod
    def _chunk_subscribers(subscribers: list[str], max_concurrent: int) -> list[list[str]]:
        chunk_len: int = math.ceil(len(subscribers) / max_concurrent)
        start_idx: Callable[[int], int] = lambda current_idx: current_idx * max_concurrent
        # fmt: off
        return [subscribers[start_idx(idx): start_idx(idx) + max_concurrent] for idx in range(0, chunk_len)]
