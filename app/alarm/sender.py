import asyncio

import aiohttp
import orjson
from aiohttp import ClientResponse

from app.alarm.repository import AlarmRedisRepository
from app.alarm.response_parser import AlarmResponseParser


class AlarmSender:
    def __init__(self, repo: AlarmRedisRepository):
        self._repo = repo

    async def send(self, subscribers: list[str], message: dict) -> None:
        # 구독 해제 유저들 제외
        unsubscribers: set[str] = await self._repo.get_unsubscribers()
        active_subscribers = self._exclude_unsubscribers(subscribers, unsubscribers)

        responses = await self._send(active_subscribers, message)

        # TODO: 재시도 구현하기
        await AlarmResponseParser(repo=self._repo).parse_all(responses)

    @staticmethod
    async def _send(subscribers: set[str], message: dict) -> ClientResponse:
        headers = {"Content-Type": "application/json"}
        url_format = "https://discord.com/api/webhooks/{0}"

        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = [session.post(url=url_format.format(key), data=orjson.dumps(message)) for key in subscribers]
            return await asyncio.gather(*tasks)

    @staticmethod
    def _exclude_unsubscribers(subscribers: list[str], unsubscribers: set[str]) -> set[str]:
        return set(subscribers) - unsubscribers
