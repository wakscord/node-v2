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
            alarms = []
            for key in subscribers:
                url = f"{DISCORD_WEBHOOK_URL}{key}"
                prepared_url, prepared_data = self._prepare_request_params(url, message)
                alarms.append(self._request(session, url=prepared_url, data=prepared_data, proxy=proxy))

            responses = await asyncio.gather(*alarms)
            return [response for response in responses if response]

    def _prepare_request_params(self, url: str, data: bytes) -> tuple[str, bytes]:
        data_str = data.decode("utf-8")
        webhook_id = url.replace(DISCORD_WEBHOOK_URL, "")

        if "{{hook_hash}}" in data_str:
            hashed_webhook = hashlib.sha256(webhook_id.encode()).hexdigest()
            data_str = data_str.replace("{{hook_hash}}", hashed_webhook)
            data = data_str.encode("utf-8")

        # Discrod Components V2 대응
        if "32768" in data_str:
            url += "?with_components=true"

        return url, data

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
                prepared_url, prepared_data = self._prepare_request_params(url=url, data=message)
                is_success = not await self._request(session, url=prepared_url, data=prepared_data, proxy=proxy)
                if is_success:
                    break
                if not remain_retry_attempt:
                    logger.warning(f"재시도 요청을 {DEFAULT_RETRY_ATTEMPT}번 모두 시도했습니다.")
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
