import asyncio

from dependency_injector.wiring import Provide, inject
from redis.asyncio import Redis

from app.alarm.sender import AlarmSender
from app.alarm.task_parser import AlarmTaskParser
from app.common.di import AppContainer
from app.common.exceptions import async_exception_handler
from app.common.settings import settings
from app.node.manager import NodeManager
from app.retry.manager import RetryManager


@inject
async def process_task(task: list[bytes], alarm_sender: AlarmSender = Provide[AppContainer.alarm_sender]) -> None:
    parser = AlarmTaskParser(task)
    await alarm_sender.send(parser.parse_subscribers(), parser.parse_message())


@async_exception_handler
async def listen(session: Redis = Provide[AppContainer.cache_session]) -> None:
    while True:
        task = await session.blpop(settings.NODE_ID)
        if task:
            await process_task(task)


@inject
async def run(
    node_manager: NodeManager = Provide[AppContainer.node_manager],
    retry_manager: RetryManager = Provide[AppContainer.retry_manager],
) -> None:
    await node_manager.join_server()
    await retry_manager.run()
    await listen()


if __name__ == "__main__":
    container = AppContainer()
    container.wire(modules=[__name__])

    asyncio.run(run())
