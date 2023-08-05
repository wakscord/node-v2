import pytest
from fakeredis.aioredis import FakeRedis

from app.alarm.repository import AlarmRedisRepository


@pytest.mark.asyncio
async def test_get_least_usage_proxy(fake_session: FakeRedis):
    proxy_key = AlarmRedisRepository._PROXIES_KEY

    # given
    least_proxy = "proxy2"
    await fake_session.zadd(proxy_key, mapping={"proxy1": 1})
    await fake_session.zadd(proxy_key, mapping={least_proxy: 0})
    repo = AlarmRedisRepository(session=fake_session)

    # when
    proxy = await repo.get_least_usage_proxy()

    # then
    assert proxy == least_proxy
    assert await fake_session.zscore(proxy_key, least_proxy) == 1


@pytest.mark.asyncio
async def test_get_least_usage_proxy_with_none_proxies(fake_session: FakeRedis):
    # given
    repo = AlarmRedisRepository(session=fake_session)
    # when
    proxy = await repo.get_least_usage_proxy()
    # then
    assert proxy is None
