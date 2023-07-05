import asyncio
import functools
import inspect
import traceback

from app.common.logger import logger
from app.common.settings import settings
from app.infra.redis import session


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
            logger.info("Stop the node server.")

        except AppException as exc:
            traceback.print_exception(exc)
            logger.warning(exc)

        finally:
            await session.hdel("node_servers", settings.NODE_ID)

    return wrapper
