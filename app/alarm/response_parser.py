from aiohttp import ClientResponse

from app.alarm.repository import AlarmRepository


class AlarmResponseParser:
    def __init__(self, repo: AlarmRepository):
        self._repo = repo

    async def parse_all(self, responses: list[ClientResponse]) -> None:
        for response in responses:
            await self.parse(response)

    async def parse(self, response: ClientResponse) -> None:
        if self._is_success(response.status):
            return

        if self._is_unsubscribe(response.status):
            return

        elif self._is_ratelimit(response.status):
            return

        return

    @staticmethod
    def _is_success(status_code: int) -> bool:
        return status_code == 204

    @staticmethod
    def _is_unsubscribe(status_code: int) -> bool:
        return status_code in [401, 403, 404]

    @staticmethod
    def _is_ratelimit(status_code: int) -> bool:
        return status_code == 429
