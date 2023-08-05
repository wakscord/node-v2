import pytest

from app.unsubscriber.repository import UnsubscriberRepository


class UnsubscriberFakeRepository(UnsubscriberRepository):
    def __init__(self):
        self._unsubscribers = set()

    async def get_unsubscribers(self) -> set[str]:
        return self._unsubscribers

    async def add_unsubscriber(self, unsubscriber: str) -> None:
        self._unsubscribers.add(unsubscriber)


@pytest.fixture(scope="function")
def unsubscriber_repo():
    return UnsubscriberFakeRepository()
