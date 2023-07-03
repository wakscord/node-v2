import asyncio
import functools
import inspect
import traceback

from app.common.logger import logger


class AppException(Exception):
    def __init__(self):
        super().__init__()


def async_exception_handler(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            if not inspect.iscoroutinefunction(func):
                raise Exception("This function is not async.")
            await func(*args, **kwargs)

        except asyncio.exceptions.CancelledError:
            logger.info("Start the node server.")
            exit()
        except AppException as exc:
            traceback.print_exception(exc)
            logger.warning(str(exc))

    return wrapper
