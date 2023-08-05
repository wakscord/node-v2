from enum import Enum

from app.common.exceptions import AppException


class AlarmSendFailedException(AppException):
    def __init__(self, message: str):
        self.message = message

    def __str__(self) -> str:
        return f"요청이 실패했습니다, ({self.message})"


class RateLimitException(AppException):
    def __str__(self) -> str:
        return "너무 많은 요청을 보내서 요청이 실패했습니다."


class UnsubscriberException(AppException):
    def __init__(self, unsubscriber: str | None):
        self.unsubscriber = unsubscriber

    def __str__(self) -> str:
        return f"구독을 해지한 유저 입니다, (key: {self.unsubscriber})"


class RequestExc(Enum):
    UNKNOWN = "전송에 실패했습니다"
    AIOHTTP_CLIENT_CONN_ERROR = "클라이언트 커넥션 에러가 발생했습니다"

    @staticmethod
    def get_message(exc: "RequestExc") -> str:
        return exc.value
