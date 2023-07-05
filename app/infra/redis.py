import asyncio

from redis.asyncio import ConnectionPool, Redis

from app.common.logger import logger
from app.common.settings import settings

pool = ConnectionPool(host=settings.REDIS_URL, port=6379, password=settings.REDIS_PASSWORD)
session: Redis = Redis(connection_pool=pool)


async def _test_ping() -> None:
    await session.ping()


try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_test_ping())

except Exception as exc:
    logger.warning(f"Redis connection error. (exception: {exc})")
    exit(0)
