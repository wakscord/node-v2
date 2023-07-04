import re

from aiohttp import ClientResponse

from app.alarm.constants import DEFAULT_RETRY_AFTER, DISCORD_WEBHOOK_URL
from app.alarm.exceptions import AlarmSendFailedException, RateLimitException
from app.alarm.repository import AlarmRepository


class AlarmResponseValidator:
    def __init__(self, repo: AlarmRepository):
        self._repo = repo

    async def is_done(self, response: ClientResponse) -> bool:
        if self._is_success(response.status):
            return True

        if self._is_unsubscribe(response.status):
            unsubscriber = self._parse_unsubscriber(response.url)
            if unsubscriber:
                await self._repo.add_unsubscriber(unsubscriber)
            return True

        elif self._is_rate_limit(response.status):
            raise await self._parse_retry_after_exception(response)

        message = f"status_code: {response.status}, body: {await response.text()}"
        raise AlarmSendFailedException(message)

    @staticmethod
    def _is_success(status_code: int) -> bool:
        return status_code == 204

    @staticmethod
    def _is_unsubscribe(status_code: int) -> bool:
        return status_code in [401, 403, 404]

    @staticmethod
    def _is_rate_limit(status_code: int) -> bool:
        return status_code == 429

    @staticmethod
    def _parse_unsubscriber(url: str) -> str | None:
        result = re.findall(pattern=f"{DISCORD_WEBHOOK_URL}(\S+)", string=url)
        return result[0] if result else None

    @staticmethod
    async def _parse_retry_after_exception(response: ClientResponse) -> RateLimitException:
        retry_after = DEFAULT_RETRY_AFTER
        is_json_response = response.headers.get("Content-Type") == "application/json"

        if is_json_response:
            json_response: dict = await response.json()
            is_global: bool = json_response.get("global", False)
            retry_after_in_json: int = json_response.get("retry_after", DEFAULT_RETRY_AFTER)

            retry_after = 60 if is_global else retry_after_in_json

        return RateLimitException(retry_after)
