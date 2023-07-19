import pytest

from app.alarm.repository import AlarmRepository


class AlarmFakeRepository(AlarmRepository):
    def __init__(self):
        self.unsubscribers = []

    async def get_unsubscribers(self) -> set[str]:
        pass

    async def add_unsubscriber(self, unsubscriber: str) -> None:
        self.unsubscribers.append(unsubscriber)

    async def get_least_usage_proxy(self) -> str | None:
        pass


@pytest.fixture
def alarm_repo():
    instance = AlarmFakeRepository()
    yield instance
