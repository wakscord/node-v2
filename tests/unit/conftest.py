import fakeredis
import pytest
from fakeredis.aioredis import FakeRedis


@pytest.fixture(scope="function")
def fake_session():
    return FakeRedis(decode_responses=True, server=fakeredis.FakeServer())
