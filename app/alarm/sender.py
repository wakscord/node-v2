import asyncio
import hashlib
import math
import traceback
from typing import Callable, Coroutine

import aiohttp
from aiohttp import BasicAuth, ClientResponse, ClientSession

from app.alarm.constants import DEFAULT_RETRY_AFTER, DEFAULT_RETRY_ATTEMPT, DISCORD_WEBHOOK_URL
from app.alarm.dtos import SendResponseDTO
from app.alarm.exceptions import AlarmSendFailedException, RateLimitException, RequestExc, UnsubscriberException
from app.alarm.repository import AlarmRepository
from app.alarm.response_validator import AlarmResponseValidator
from app.common.logger import logger
from app.common.settings import settings
from app.unsubscriber.repository import UnsubscriberRepository


class AlarmService:
    _headers = {"Content-Type": "application/json"}

    def __init__(
        self,
        alarm_repo: AlarmRepository,
        unsubscriber_repo: UnsubscriberRepository,
    ):
        self._alarm_repo = alarm_repo
        self._unsubscriber_repo = unsubscriber_repo

    async def send(self, subscribers: list[str], message: bytes) -> list[Coroutine]:
        should_retry_alarms = []
        chunked_subscribers_list = self._chunk_subscribers(subscribers, settings.MAX_CONCURRENT)

        for chunked_subscribers in chunked_subscribers_list:
            failed_subscribers: list[str] = await self._send(chunked_subscribers, message)
            if not failed_subscribers:
                continue
            should_retry_alarms.extend(await self._create_retry_task(failed_subscribers, message))

        return should_retry_alarms

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
        # 웹훅 URL에서 ID 부분 추출
        webhook_id = url.replace(DISCORD_WEBHOOK_URL, "")

        # 메시지에 {{hook_hash}} 식별자가 있는지 확인
        try:
            # 바이트를 문자열로 변환 (JSON 내용)
            data_str = data.decode("utf-8")

            if "{{hook_hash}}" in data_str:
                # 웹훅 ID 해싱 (SHA-256 사용)
                hashed_webhook = hashlib.sha256(webhook_id.encode()).hexdigest()
                # {{hook_hash}}를 해시된 웹훅 ID로 대체
                data_str = data_str.replace("{{hook_hash}}", hashed_webhook)
                # 문자열을 다시 바이트로 변환
                data = data_str.encode("utf-8")
        except UnicodeDecodeError as e:
            logger.warning(f"메시지 데이터 디코딩 오류: {e}")
        except Exception as e:
            # 오류 로깅 후 원본 데이터로 계속 진행
            logger.warning(f"hook_hash 처리 중 오류 발생: {e}")

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
            exc_message = RequestExc.get_message(RequestExc.AIOHTTP_CLIENT_CONN_ERROR)
            logger.warning(f"{exc_message}, (exception: {exc})")
        except Exception as exc:
            exc_message = RequestExc.get_message(RequestExc.UNKNOWN)
            logger.warning(f"{exc_message}, (exception: {exc}\n{traceback.format_exc()})")
        return url

    async def _create_retry_task(self, failed_subscribers: list[str], message: bytes) -> list[Coroutine]:
        proxy = await self._alarm_repo.get_least_usage_proxy()
        return [self._retry(url=subscriber, message=message, proxy=proxy) for subscriber in failed_subscribers]

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
