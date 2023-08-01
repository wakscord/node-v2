import asyncio

from dependency_injector.wiring import Provide, inject

from app.alarm.sender import AlarmSender
from app.common.di import AppContainer
from app.common.exceptions import async_exception_handler
from app.common.process_status import process_status_handler
from app.common.utils.task_parser import TaskParser
from app.node.manager import NodeManager
from app.unsubscriber.service import UnsubscriberService


@process_status_handler
@inject
async def process_task(
    task: tuple[str, str],
    alarm_sender: AlarmSender = Provide[AppContainer.alarm_sender],
    unsubscriber_service: UnsubscriberService = Provide[AppContainer.unsubscriber_service],
) -> None:
    parser = TaskParser(task)
    active_subscribers = await unsubscriber_service.exclude_unsubscribers(parser.parse_subscribers())
    await alarm_sender.send(active_subscribers, parser.parse_message())


@async_exception_handler
@inject
async def run(node_manager: NodeManager = Provide[AppContainer.node_manager]) -> None:
    await node_manager.join_server()
    while True:
        task = await node_manager.pop_task()
        if task:
            await process_task(task)


if __name__ == "__main__":
    container = AppContainer()
    container.wire(modules=[__name__])

    asyncio.run(run())
