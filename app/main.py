import asyncio

from app.alarm.repository import AlarmRedisRepository
from app.alarm.sender import AlarmSender
from app.alarm.task_parser import AlarmTaskParser
from app.common.exceptions import async_exception_handler
from app.common.logger import logger
from app.common.settings import settings
from app.infra.redis import session
from app.node.repository import NodeRedisRepository


@async_exception_handler
async def process_task(task: list[bytes]) -> None:
    parser = AlarmTaskParser(task)
    sender = AlarmSender(repo=AlarmRedisRepository(session))
    await sender.send(parser.parse_subscribers(), parser.parse_message())


async def join_server() -> None:
    node_repo = NodeRedisRepository(session)
    await node_repo.join()


@async_exception_handler
async def listen() -> None:
    logger.info(f"Start the node server. (node_id: {settings.NODE_ID})")
    asyncio.create_task(join_server())

    while True:
        task = await session.blpop(settings.NODE_ID)
        if task:
            asyncio.create_task(process_task(task))


async def test_redis_ping() -> None:
    try:
        await session.ping()
    except Exception as exc:
        logger.warning(f"Redis connection error. (exception: {exc})")
        exit(0)


async def run() -> None:
    await test_redis_ping()
    await listen()


if __name__ == "__main__":
    asyncio.run(run())
