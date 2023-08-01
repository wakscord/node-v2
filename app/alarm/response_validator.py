import re

import yarl

from app.alarm.constants import DISCORD_WEBHOOK_URL
from app.alarm.dtos import SendResponseDTO
from app.alarm.exceptions import AlarmSendFailedException, RateLimitException, UnsubscriberException


class AlarmResponseValidator:
    @classmethod
    async def is_done(cls, response: SendResponseDTO) -> bool:
        if cls._is_success(response.status):
            return True

        if cls._is_unsubscribe(response.status):
            unsubscriber = cls._parse_unsubscriber(response.url)
            raise UnsubscriberException(unsubscriber)

        elif cls._is_rate_limit(response.status):
            raise RateLimitException()

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
    def _parse_unsubscriber(url: yarl.URL) -> str | None:
        pattern = r"{0}(\S+)".format(DISCORD_WEBHOOK_URL)
        result = re.findall(pattern=pattern, string=str(url))
        return result[0] if result else None
