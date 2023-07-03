import asyncio

from app.alarm.repository import AlarmRedisRepository
from app.alarm.sender import AlarmSender
from app.alarm.task_parser import AlarmTaskParser
from app.common.exceptions import async_exception_handler
from app.common.logger import logger
from app.common.settings import settings
from app.infra.redis import session


@async_exception_handler
async def process_task(task: list[bytes]):
    parser = AlarmTaskParser(task)
    sender = AlarmSender(repo=AlarmRedisRepository(session))
    await sender.send(parser.parse_subscribers(), parser.parse_message())


@async_exception_handler
async def listen() -> None:
    logger.info("Start the node server.")
    while True:
        task = await session.blpop(f"node-{settings.NODE_ID}")
        if task:
            await process_task(task)


if __name__ == "__main__":
    asyncio.run(listen())
