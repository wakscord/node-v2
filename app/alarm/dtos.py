from dataclasses import dataclass
from typing import Awaitable, Callable


@dataclass(frozen=True)
class SendResponseDTO:
    url: str
    status: int
    text: Callable[[], Awaitable[str]]
