from redis.asyncio import ConnectionPool, Redis

from app.common.settings import settings

pool = ConnectionPool(host=settings.REDIS_URL, port=6379, password=settings.REDIS_PASSWORD, decode_responses=True)
session: Redis = Redis(connection_pool=pool)
