import asyncio
import math
import traceback
from typing import Callable

import aiohttp
import orjson
import redis.exceptions
from aiohttp import BasicAuth, ClientResponse, ClientSession

from app.alarm.constants import DEFAULT_RETRY_AFTER, DEFAULT_RETRY_ATTEMPT, DISCORD_WEBHOOK_URL
from app.alarm.dtos import SendResponseDTO
from app.alarm.exceptions import AlarmSendFailedException, RateLimitException
from app.alarm.repository import AlarmRedisRepository
from app.alarm.response_validator import AlarmResponseValidator
from app.common.logger import logger
from app.common.settings import settings
from app.retry.rate_limiter import RetryRateLimiter


class AlarmSender:
    _headers = {"Content-Type": "application/json"}

    def __init__(self, repo: AlarmRedisRepository, retry_rate_limiter: RetryRateLimiter):
        self._repo = repo
        self.retry_rate_limiter = retry_rate_limiter

    async def send(self, subscribers: list[str], message: dict) -> None:
        unsubscribers: set[str] = await self._repo.get_unsubscribers()
        active_subscribers = self._exclude_unsubscribers(subscribers, unsubscribers)
        await self._send(active_subscribers, message)

    async def _send(self, subscribers: set[str], message: dict) -> None:
        data = orjson.dumps(message)
        chunked_subscribers_list = self._chunk_subscribers(list(subscribers), settings.MAX_CONCURRENT)
        for chunked_subscribers in chunked_subscribers_list:
            proxy = await self._repo.get_least_usage_proxy()
            async with aiohttp.ClientSession(headers=self._headers) as session:
                alarms = [
                    self._request(session, url=f"{DISCORD_WEBHOOK_URL}{key}", data=data, proxy=proxy)
                    for key in chunked_subscribers
                ]
                result = await asyncio.gather(*alarms)

            failed_alarms = [alarm for alarm in result if alarm]
            if failed_alarms:
                proxy = await self._repo.get_least_usage_proxy()
                retry_alarms = [self._retry(url=subscriber, data=data, proxy=proxy) for subscriber in failed_alarms]
                self.retry_rate_limiter.add_alarms(retry_alarms)

    async def _request(self, session: ClientSession, url: str, data: bytes, proxy: str | None) -> str | None:
        proxy_auth = BasicAuth(settings.PROXY_USER, settings.PROXY_PASSWORD) if proxy else None
        try:
            response: ClientResponse = await session.post(url=url, data=data, proxy=proxy, proxy_auth=proxy_auth)
            response_dto = SendResponseDTO(url=response.url, status=response.status, text=response.text)
            await AlarmResponseValidator(self._repo).is_done(response_dto)
            return None
        except (RateLimitException, AlarmSendFailedException) as exc:
            logger.warning(exc)
        except aiohttp.ClientConnectionError as exc:
            logger.warning(f"클라이언트 커넥션 에러가 발생했습니다, (exception: {exc})")
        except redis.exceptions.ConnectionError as exc:
            # TODO: 레디스 커넥션 이슈 해결 시 해당 로직 제거
            logger.warning(f"레디스 커넥션 에러가 발생했습니다. 서버를 재시작 합니다, (exception: {exc}\n{traceback.format_exc()})")
            exit(0)
        except Exception as exc:
            logger.warning(f"전송에 실패했습니다, (exception: {exc}\n{traceback.format_exc()})")
        return url

    async def _retry(self, url: str, data: bytes, proxy: str | None) -> None:
        remain_retry_attempt = DEFAULT_RETRY_ATTEMPT
        async with aiohttp.ClientSession(headers=self._headers) as session:
            while True:
                is_success = not await self._request(session, url=url, data=data, proxy=proxy)
                if is_success or not remain_retry_attempt:
                    break
                remain_retry_attempt -= 1
                current_retry_attempt = DEFAULT_RETRY_ATTEMPT - remain_retry_attempt
                await asyncio.sleep(current_retry_attempt * DEFAULT_RETRY_AFTER)

    @staticmethod
    def _exclude_unsubscribers(subscribers: list[str], unsubscribers: set[str]) -> set[str]:
        return set(subscribers) - unsubscribers

    @staticmethod
    def _chunk_subscribers(subscribers: list[str], max_concurrent: int) -> list[list[str]]:
        chunk_len: int = math.ceil(len(subscribers) / max_concurrent)
        start_idx: Callable[[int], int] = lambda current_idx: current_idx * max_concurrent
        # fmt: off
        return [subscribers[start_idx(idx): start_idx(idx) + max_concurrent] for idx in range(0, chunk_len)]
