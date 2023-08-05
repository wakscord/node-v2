import asyncio
from typing import Coroutine

from dependency_injector.wiring import Provide, inject
from orjson import orjson

from app.alarm.sender import AlarmService
from app.common.di import AppContainer
from app.common.exceptions import async_exception_handler
from app.common.process_status import process_status_handler
from app.common.utils.task_parser import TaskParser
from app.node.manager import NodeManager
from app.retry.rate_limiter import RetryRateLimiter
from app.unsubscriber.service import UnsubscriberService


@process_status_handler
@inject
async def process_task(
    task: tuple[str, str],
    alarm_service: AlarmService = Provide[AppContainer.alarm_service],
    unsubscriber_service: UnsubscriberService = Provide[AppContainer.unsubscriber_service],
) -> list[Coroutine]:
    parser = TaskParser(task)
    request_subscribers = parser.parse_subscribers()
    request_message = parser.parse_message()

    active_subscribers: list[str] = await unsubscriber_service.exclude_unsubscribers(request_subscribers)
    message: bytes = orjson.dumps(request_message)

    failed_alarms = await alarm_service.send(active_subscribers, message)
    return failed_alarms


@async_exception_handler
@inject
async def run(
    node_manager: NodeManager = Provide[AppContainer.node_manager],
    retry_rate_limiter: RetryRateLimiter = Provide[AppContainer.retry_rate_limiter],
) -> None:
    await node_manager.join_server()
    await retry_rate_limiter.watch_retry()

    while True:
        task = await node_manager.pop_task()
        if task:
            failed_alarms = await process_task(task)
            retry_rate_limiter.add_alarms(failed_alarms)


if __name__ == "__main__":
    container = AppContainer()
    container.wire(modules=[__name__])

    asyncio.run(run())
