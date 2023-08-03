from dataclasses import dataclass

import pytest
from aiohttp import BasicAuth

from app.alarm.repository import AlarmRepository
from app.unsubscriber.repository import UnsubscriberRepository


class AlarmFakeRepository(AlarmRepository):
    async def get_least_usage_proxy(self) -> str | None:
        pass


class UnsubscriberFakeRepository(UnsubscriberRepository):
    async def get_unsubscribers(self) -> set[str]:
        pass

    async def add_unsubscriber(self, unsubscriber: str) -> None:
        pass


@pytest.fixture(scope="function")
def alarm_repo():
    return AlarmFakeRepository()


@pytest.fixture(scope="function")
def unsubscriber_repo():
    return UnsubscriberFakeRepository()


@dataclass(frozen=True)
class AiohttpFakeResponse:
    url: str
    status: int
    text: str


class AiohttpFakeClientSession:
    def __init__(self, response_status: int):
        self._status: int = response_status
        self._raise_exception = False
        self._exception = Exception

    def _set_proxy(self, proxy: str):
        self._proxy = proxy

    def _set_proxy_auth(self, proxy_auth: BasicAuth):
        self._proxy_auth = proxy_auth

    def enable_raise_exception(self, exception: Exception | None = None):
        if exception:
            self._exception = exception
        self._raise_exception = True

    async def post(self, url=None, data=None, proxy=None, proxy_auth=None):
        self._set_proxy(proxy)
        self._set_proxy_auth(proxy_auth)
        if self._raise_exception:
            raise self._exception
        return AiohttpFakeResponse(url=url, status=self._status, text=data)
