import pytest

from app.unsubscriber.service import UnsubscriberService
from tests.unit.unsubscriber.conftest import UnsubscriberFakeRepository


@pytest.mark.asyncio
async def test_exclude_unsubscribers(unsubscriber_repo: UnsubscriberFakeRepository):
    # given
    subscribers = {"subscriber1", "subscriber2"}
    unsubscriber_repo._unsubscribers = {"subscriber1"}

    # when
    service = UnsubscriberService(repo=unsubscriber_repo)
    active_subscribers = await service.exclude_unsubscribers(subscribers)

    # then
    assert active_subscribers == ["subscriber2"]
