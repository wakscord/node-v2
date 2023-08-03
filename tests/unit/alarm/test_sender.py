import asyncio
from typing import Coroutine
from unittest.mock import AsyncMock

import aiohttp
import pytest
from pytest_mock import MockerFixture

from app.alarm.constants import DEFAULT_RETRY_ATTEMPT, DISCORD_WEBHOOK_URL
from app.alarm.exceptions import RequestExc
from app.alarm.repository import AlarmRepository
from app.alarm.sender import AlarmService
from app.unsubscriber.repository import UnsubscriberRepository
from tests.unit.alarm.conftest import AiohttpFakeClientSession


def test_chunk_subscribers():
    # given
    subscribers: list[str] = ["subscriber" for _ in range(5)]
    max_concurrent: int = 2
    # when
    chunked = AlarmService._chunk_subscribers(subscribers, max_concurrent)
    # then
    assert len(chunked) == 3


@pytest.mark.asyncio
async def test_retry_attempt(
    mocker: MockerFixture, alarm_repo: AlarmRepository, unsubscriber_repo: UnsubscriberRepository
):
    # given
    service = AlarmService(alarm_repo, unsubscriber_repo)
    mocker.patch("app.alarm.sender.AlarmService._request", return_value="failed_url")
    sleep_patcher = mocker.patch("asyncio.sleep", new_callable=AsyncMock)
    # when
    await service._retry(url="", message="", proxy="")
    # then
    assert sleep_patcher.await_count == DEFAULT_RETRY_ATTEMPT


@pytest.mark.asyncio
async def test_create_retry_task(
    mocker: MockerFixture, alarm_repo: AlarmRepository, unsubscriber_repo: UnsubscriberRepository
):
    # given
    subscriber_count = 5
    failed_subscribers = [f"subscriber{i}" for i in range(subscriber_count)]
    service = AlarmService(alarm_repo, unsubscriber_repo)
    mocker.patch("app.alarm.sender.AlarmService._retry", new_callable=AsyncMock)
    # when
    retry_tasks = await service._create_retry_task(failed_subscribers, message="")
    # then
    assert len(retry_tasks) == subscriber_count
    await asyncio.gather(*retry_tasks)


@pytest.mark.asyncio
async def test_request_success(
    alarm_repo: AlarmRepository,
    unsubscriber_repo: UnsubscriberRepository,
):
    # given
    service = AlarmService(alarm_repo, unsubscriber_repo)
    aiohttp_session = AiohttpFakeClientSession(response_status=204)
    # when
    result = await service._request(aiohttp_session, url="", data="", proxy=None)
    # then
    assert result is None


@pytest.mark.asyncio
async def test_request_rate_limit(
    mocker: MockerFixture,
    alarm_repo: AlarmRepository,
    unsubscriber_repo: UnsubscriberRepository,
):
    service = AlarmService(alarm_repo, unsubscriber_repo)
    logger_patcher = mocker.patch("app.common.logger.logger.warning")

    # given
    subscriber = "subscriber"
    aiohttp_session = AiohttpFakeClientSession(response_status=429)
    # when
    result = await service._request(aiohttp_session, url=subscriber, data="", proxy=None)
    # then
    assert result == subscriber
    logger_patcher.assert_called_once()


@pytest.mark.asyncio
async def test_request_with_raise_unknown_exception(
    mocker: MockerFixture,
    alarm_repo: AlarmRepository,
    unsubscriber_repo: UnsubscriberRepository,
):
    service = AlarmService(alarm_repo, unsubscriber_repo)
    logger_patcher = mocker.patch("app.common.logger.logger.warning")

    # given
    aiohttp_session = AiohttpFakeClientSession(response_status=204)
    aiohttp_session.enable_raise_exception()
    exc_message = RequestExc.get_message(RequestExc.UNKNOWN)
    # when
    await service._request(aiohttp_session, url="", data="", proxy=None)
    # then
    assert exc_message in logger_patcher.call_args[0][0]


@pytest.mark.asyncio
async def test_request_with_aiohttp_conn_error(
    mocker: MockerFixture,
    alarm_repo: AlarmRepository,
    unsubscriber_repo: UnsubscriberRepository,
):
    service = AlarmService(alarm_repo, unsubscriber_repo)
    logger_patcher = mocker.patch("app.common.logger.logger.warning")

    # given
    aiohttp_session = AiohttpFakeClientSession(response_status=204)
    aiohttp_session.enable_raise_exception(exception=aiohttp.ClientConnectionError)
    exc_message = RequestExc.get_message(RequestExc.AIOHTTP_CLIENT_CONN_ERROR)
    # when
    await service._request(aiohttp_session, url="", data="", proxy=None)
    # then
    assert exc_message in logger_patcher.call_args[0][0]


@pytest.mark.asyncio
async def test_request_with_unsubscriber(
    mocker: MockerFixture,
    alarm_repo: AlarmRepository,
    unsubscriber_repo: UnsubscriberRepository,
):
    service = AlarmService(alarm_repo, unsubscriber_repo)
    spy_unsubscriber_repo = mocker.spy(unsubscriber_repo, "add_unsubscriber")
    # given
    unsubscriber = "12345678/webhook"
    aiohttp_session = AiohttpFakeClientSession(response_status=404)
    # when
    await service._request(aiohttp_session, url=f"{DISCORD_WEBHOOK_URL}{unsubscriber}", data="", proxy=None)
    # then
    assert unsubscriber == spy_unsubscriber_repo.call_args[0][0]


@pytest.mark.asyncio
async def test_request_with_unsubscriber_if_invalid_url(
    mocker: MockerFixture,
    alarm_repo: AlarmRepository,
    unsubscriber_repo: UnsubscriberRepository,
):
    service = AlarmService(alarm_repo, unsubscriber_repo)
    spy_unsubscriber_repo = mocker.spy(unsubscriber_repo, "add_unsubscriber")
    # given
    unsubscriber = "12345678/webhook"
    aiohttp_session = AiohttpFakeClientSession(response_status=404)
    # when
    await service._request(aiohttp_session, url=unsubscriber, data="", proxy=None)
    # then
    assert spy_unsubscriber_repo.call_args is None


@pytest.mark.asyncio
async def test_private_send_if_failed_return_url(
    mocker: MockerFixture,
    alarm_repo: AlarmRepository,
    unsubscriber_repo: UnsubscriberRepository,
):
    service = AlarmService(alarm_repo, unsubscriber_repo)
    # given
    failed_subscriber_count = 10
    failed_subscribers = ["subscriber" for _ in range(failed_subscriber_count)]
    mocker.patch("app.alarm.sender.AlarmService._request", return_value="url")
    # when
    responses = await service._send(subscribers=failed_subscribers, message="")
    # then
    assert len(responses) == failed_subscriber_count
    assert isinstance(responses[0], str)


@pytest.mark.asyncio
async def test_private_send_if_success_return_none(
    mocker: MockerFixture,
    alarm_repo: AlarmRepository,
    unsubscriber_repo: UnsubscriberRepository,
):
    service = AlarmService(alarm_repo, unsubscriber_repo)
    # given
    subscribers = ["subscriber" for _ in range(10)]
    mocker.patch("app.alarm.sender.AlarmService._request", return_value=None)
    # when
    responses = await service._send(subscribers=subscribers, message="")
    # then
    assert len(responses) == 0


@pytest.mark.asyncio
async def test_send_if_failed_return_task(
    mocker: MockerFixture,
    alarm_repo: AlarmRepository,
    unsubscriber_repo: UnsubscriberRepository,
):
    service = AlarmService(alarm_repo, unsubscriber_repo)

    # given
    failed_subscriber_count = 10
    failed_subscribers = ["subscriber" for _ in range(failed_subscriber_count)]
    mocker.patch("app.alarm.sender.AlarmService._request", return_value="url")
    mocker.patch("app.alarm.sender.AlarmService._retry", return_value=None)
    # when
    failed_alarms = await service.send(subscribers=failed_subscribers, message="")
    # then
    assert len(failed_alarms) == failed_subscriber_count
    assert isinstance(failed_alarms[0], Coroutine)

    # clear
    await asyncio.gather(*failed_alarms)


@pytest.mark.asyncio
async def test_send_if_success_return_none(
    mocker: MockerFixture,
    alarm_repo: AlarmRepository,
    unsubscriber_repo: UnsubscriberRepository,
):
    service = AlarmService(alarm_repo, unsubscriber_repo)
    # given
    subscribers = ["subscriber" for _ in range(10)]
    mocker.patch("app.alarm.sender.AlarmService._request", return_value=None)
    # when
    failed_alarms = await service.send(subscribers=subscribers, message="")
    # then
    assert len(failed_alarms) == 0
