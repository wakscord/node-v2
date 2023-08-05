import pytest
from fakeredis.aioredis import FakeRedis

from app.unsubscriber.repository import UnsubscriberRedisRepository


@pytest.mark.asyncio
async def test_add_and_get_unsubscribers(fake_session: FakeRedis):
    # given
    subscriber1, subscriber2 = ["test1", "test2"]
    repo = UnsubscriberRedisRepository(session=fake_session)

    # when
    await repo.add_unsubscriber(unsubscriber=subscriber1)
    await repo.add_unsubscriber(unsubscriber=subscriber2)

    # then
    assert {subscriber1, subscriber2} == await repo.get_unsubscribers()
