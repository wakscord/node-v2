import pytest
import yarl

from app.alarm.constants import DISCORD_WEBHOOK_URL
from app.alarm.dtos import SendResponseDTO
from app.alarm.exceptions import AlarmSendFailedException, RateLimitException, UnsubscriberException
from app.alarm.response_validator import AlarmResponseValidator


def test_success_status_code():
    # given
    status_code = 204
    # when
    result = AlarmResponseValidator._is_success(status_code=status_code)
    # then
    assert result


def test_unsubscribe_status_code():
    # given
    status_codes = [401, 403, 404]
    # when
    result = [AlarmResponseValidator._is_unsubscribe(status_code=status_code) for status_code in status_codes]
    # then
    assert all(result)


def test_rate_limit_status_code():
    # given
    status_code = 429
    # when
    result = AlarmResponseValidator._is_rate_limit(status_code=status_code)
    # then
    assert result


def test_parse_unsubscriber_success():
    # given
    raw_webhook_uri = "12345678/webhook"
    url = yarl.URL(f"{DISCORD_WEBHOOK_URL}{raw_webhook_uri}")
    # when
    parsed_unsubscriber = AlarmResponseValidator._parse_unsubscriber(url=url)
    # then
    assert parsed_unsubscriber == raw_webhook_uri


def test_parse_unsubscriber_none_parse_url():
    # given
    raw_webhook_url = "https://test.discord.com/12345678/webhook"
    # when
    parsed_unsubscriber = AlarmResponseValidator._parse_unsubscriber(url=raw_webhook_url)
    # then
    assert parsed_unsubscriber is None


@pytest.mark.asyncio
async def test_is_done_success():
    # given
    response = SendResponseDTO(url=None, status=204, text=None)
    # when
    result = await AlarmResponseValidator.validate(response)
    # then
    assert result is None


@pytest.mark.asyncio
async def test_is_done_rate_limit():
    # given
    response = SendResponseDTO(url=None, status=429, text=None)
    # then
    with pytest.raises(RateLimitException):
        # when
        await AlarmResponseValidator.validate(response)


@pytest.mark.asyncio
async def test_is_done_internal_error():
    # given
    error_msg = "This is test"

    async def text() -> str:
        return error_msg

    response = SendResponseDTO(url=None, status=500, text=text)
    # then
    with pytest.raises(AlarmSendFailedException) as exc:
        # when
        await AlarmResponseValidator.validate(response)
    assert error_msg in str(exc.value)


@pytest.mark.asyncio
async def test_is_done_unsubscriber_success():
    # given
    response = SendResponseDTO(url=None, status=404, text=None)
    # when
    with pytest.raises(UnsubscriberException):
        await AlarmResponseValidator.validate(response)


@pytest.mark.asyncio
async def test_is_done_unsubscriber_failed_parse_url():
    # given
    raw_webhook_uri = "12345678/webhook"
    url = yarl.URL(f"{DISCORD_WEBHOOK_URL}{raw_webhook_uri}")
    response = SendResponseDTO(url=url, status=401, text=None)
    # when
    exc: UnsubscriberException
    with pytest.raises(UnsubscriberException) as exc:
        await AlarmResponseValidator.validate(response)
        # then
        assert exc.unsubscriber == raw_webhook_uri
