import os
import socket
from dataclasses import dataclass
from typing import Callable

from dotenv import dotenv_values, find_dotenv

is_prod = os.getenv("ENV") == "PROD"

env_path = "/run/secrets/wakscord-env" if is_prod else find_dotenv()
if not os.path.exists(env_path):
    raise Exception("Dotenv is not exists.")


@dataclass(frozen=True)
class Settings:
    NODE_ID: str
    MAX_CONCURRENT: int
    REDIS_URL: str
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    PROXY_USER: str | None = None
    PROXY_PASSWORD: str | None = None


to_int: Callable[[str, int], int] = lambda value, else_value: int(value) if value else else_value

raw_settings = dotenv_values(env_path)
settings = Settings(
    NODE_ID=f"node_{socket.gethostname()}",
    MAX_CONCURRENT=to_int(raw_settings.get("MAX_CONCURRENT"), 2000),
    REDIS_URL=raw_settings.get("REDIS_URL") or "localhost",
    REDIS_PORT=to_int(raw_settings.get("REDIS_PORT"), 6379),
    REDIS_PASSWORD=raw_settings.get("REDIS_PASSWORD"),
    PROXY_USER=raw_settings.get("PROXY_USER"),
    PROXY_PASSWORD=raw_settings.get("PROXY_PASSWORD"),
)
