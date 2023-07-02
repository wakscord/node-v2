import functools
import traceback

from app.common.logger import logger


class AppException(Exception):
    def __init__(self):
        super().__init__()


def exception_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except KeyboardInterrupt:
            logger.info("Start the node server.")
            exit()
        except AppException as exc:
            traceback.print_exception(exc)
            logger.warning(str(exc))

    return wrapper
