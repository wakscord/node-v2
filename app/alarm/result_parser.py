from httpx._models import Response
from redis import Redis

from app.alarm.exceptions import AlarmSendFailedException, RateLimitException

DEFAULT_RETRY_AFTER: int = 3
UNSUBSCRIBERS_KEY = "unsubscribers"


class AlarmResultParser:
    def __init__(self, session: Redis):
        self._session = session

    def parse(self, key: str, result: Response) -> None:
        if self._is_success(result.status_code):
            return

        if self._is_unsubscribe(result.status_code):
            return self._add_unsubscribe_key(key=key)

        elif self._is_ratelimit(result.status_code):
            raise self._parse_retry_after_exception(response=result)

        raise AlarmSendFailedException(message=f"status_code: {result.status_code}, body: {str(result.content)}")

    @staticmethod
    def _is_success(status_code: int) -> bool:
        return status_code == 204

    @staticmethod
    def _is_unsubscribe(status_code: int) -> bool:
        return status_code in [401, 403, 404]

    @staticmethod
    def _is_ratelimit(status_code: int) -> bool:
        return status_code == 429

    @staticmethod
    def _parse_retry_after_exception(response: Response) -> RateLimitException:
        retry_after = DEFAULT_RETRY_AFTER
        has_json_response = response.headers.get("Content-Type") == "application/json"

        if has_json_response:
            json_response = response.json()
            if json_response.get("retry_after"):
                pre_retry_after = round(json_response.get("retry_after") + 0.5)
                retry_after = min(DEFAULT_RETRY_AFTER, pre_retry_after)

            if json_response.get("global"):
                retry_after = 60

        return RateLimitException(retry_after=retry_after)

    def _add_unsubscribe_key(self, key: str) -> None:
        self._session.sadd(UNSUBSCRIBERS_KEY, key)
