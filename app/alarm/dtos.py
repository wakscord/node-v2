from dataclasses import dataclass
from typing import Awaitable, Callable

import yarl


@dataclass(frozen=True)
class SendResponseDTO:
    url: yarl.URL
    status: int
    text: Callable[[], Awaitable[str]]
