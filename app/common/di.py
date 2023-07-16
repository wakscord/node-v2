from dependency_injector import containers, providers
from redis.asyncio import BlockingConnectionPool, Redis

from app.alarm.repository import AlarmRedisRepository
from app.alarm.sender import AlarmSender
from app.common.settings import settings
from app.node.manager import NodeManager
from app.retry.manager import RetryManager


class AppContainer(containers.DeclarativeContainer):
    redis_connection_pool = providers.Factory(
        BlockingConnectionPool,
        host=settings.REDIS_URL,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
        max_connections=30,
        timeout=None,
    )
    redis_session = providers.Factory(Redis, connection_pool=redis_connection_pool)

    retry_manager = providers.Singleton(RetryManager)

    alarm_repository = providers.Singleton(AlarmRedisRepository, session=redis_session)
    alarm_sender = providers.Singleton(AlarmSender, repo=alarm_repository, retry_manager=retry_manager)

    node_manager = providers.Singleton(NodeManager, node_id=settings.NODE_ID, session=redis_session)
