from app.unsubscriber.repository import UnsubscriberRepository


class UnsubscriberService:
    def __init__(self, repo: UnsubscriberRepository):
        self._repo = repo

    async def exclude_unsubscribers(self, subscribers: list[str]) -> set[str]:
        unsubscribers: set[str] = await self._repo.get_unsubscribers()
        return set(subscribers) - unsubscribers
