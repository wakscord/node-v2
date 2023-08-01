from app.unsubscriber.repository import UnsubscriberRepository


class UnsubscriberService:
    def __init__(self, repo: UnsubscriberRepository):
        self._repo = repo

    async def exclude_unsubscribers(self, subscribers: list[str]) -> list[str]:
        unsubscribers: set[str] = await self._repo.get_unsubscribers()
        return list(set(subscribers) - unsubscribers)
