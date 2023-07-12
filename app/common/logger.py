import logging
from logging import Logger

logging.basicConfig(
    format="[%(name)s] (%(asctime)s) %(levelname)s: %(message)s",
    datefmt="%y/%m/%d %p %I:%M:%S",
    level=logging.INFO,
)
logger: Logger = logging.getLogger("node")
