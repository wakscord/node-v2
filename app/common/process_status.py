import functools
from enum import Enum


def process_status_handler(func):  # type: ignore
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):  # type: ignore
        manager.start()
        result = await func(*args, **kwargs)

        manager.complete()
        return result

    return wrapper


class ProcessStatus(Enum):
    RUNNING = "running"
    WAITING = "waiting"


class ProcessStatusManager:
    def __init__(self) -> None:
        self._status = ProcessStatus.WAITING

    def start(self) -> None:
        self._status = ProcessStatus.RUNNING

    def complete(self) -> None:
        self._status = ProcessStatus.WAITING

    def get_current(self) -> ProcessStatus:
        return self._status


manager = ProcessStatusManager()
