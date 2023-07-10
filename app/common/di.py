from dependency_injector import containers, providers
from redis.asyncio import ConnectionPool, Redis

from app.alarm.repository import AlarmRedisRepository
from app.alarm.sender import AlarmSender
from app.common.settings import settings
from app.node.manager import NodeManager


class AppContainer(containers.DeclarativeContainer):
    redis_connection_pool = providers.Resource(
        ConnectionPool, host=settings.REDIS_URL, port=6379, password=settings.REDIS_PASSWORD, decode_responses=True
    )
    redis_session = providers.Resource(Redis, connection_pool=redis_connection_pool)

    alarm_repository = providers.Singleton(AlarmRedisRepository, session=redis_session)
    alarm_sender = providers.Singleton(AlarmSender, repo=alarm_repository)

    node_manager = providers.Singleton(NodeManager, node_id=settings.NODE_ID, session=redis_session)
