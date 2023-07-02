from celery import Celery

from app.alarm.sender import AlarmSender
from app.alarm.task_parser import AlarmTaskParser
from app.common.exceptions import exception_handler
from app.common.logger import logger
from app.common.settings import settings
from app.infra import celeryconfig
from app.infra.redis import session

worker = Celery()
worker.config_from_object(celeryconfig)


@exception_handler
def process_task(task: list[bytes]):
    parser = AlarmTaskParser(raw_task=task)
    AlarmSender.send(session=session, subscribers=parser.parse_subscribers(), message=parser.parse_message())


@exception_handler
def listen() -> None:
    logger.info("Start the node server.")
    while True:
        task = session.blpop(f"node-{settings.NODE_ID}")
        if task:
            process_task(task=task)


if __name__ == "__main__":
    listen()
