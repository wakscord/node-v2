import asyncio
import functools
import inspect
import traceback

from app.common.logger import logger


class AppException(Exception):
    def __init__(self) -> None:
        super().__init__()


def async_exception_handler(func):  # type: ignore
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):  # type: ignore
        try:
            if not inspect.iscoroutinefunction(func):
                raise Exception("This function is not async.")
            return await func(*args, **kwargs)

        except asyncio.exceptions.CancelledError:
            logger.info("Stop the node server.")

        except AppException as exc:
            traceback.print_exception(exc)
            logger.warning(exc)

    return wrapper
