from dependency_injector import containers, providers
from redis.asyncio import BlockingConnectionPool, Redis

from app.alarm.repository import AlarmRedisRepository
from app.alarm.sender import AlarmSender
from app.common.settings import settings
from app.node.manager import NodeManager
from app.retry.rate_limiter import RetryRateLimiter


class CacheContainer(containers.DeclarativeContainer):
    redis_connection_pool = providers.Factory(
        BlockingConnectionPool,
        host=settings.REDIS_URL,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
        max_connections=30,
        socket_keepalive=True,
        socket_timeout=300,
        timeout=10,
    )
    redis_session = providers.Factory(Redis, connection_pool=redis_connection_pool)


class AppContainer(containers.DeclarativeContainer):
    cache_session = CacheContainer.redis_session

    retry_rate_limiter = providers.Singleton(RetryRateLimiter)
    alarm_repository = providers.Singleton(AlarmRedisRepository, session=cache_session)
    alarm_sender = providers.Singleton(AlarmSender, repo=alarm_repository, retry_rate_limiter=retry_rate_limiter)
    node_manager = providers.Singleton(NodeManager, node_id=settings.NODE_ID, session=cache_session)
