from app.common.exceptions import AppException


class ParseInvalidArgumentException(AppException):
    def __init__(self, message: str):
        self.message = message

    def __str__(self) -> str:
        return f"올바른 요청 인자가 아닙니다, ({self.message})"


class ParseInvalidFormatException(AppException):
    def __init__(self, message: str):
        self.message = message

    def __str__(self) -> str:
        return f"올바른 요청 형식이 아닙니다, ({self.message})"


class AlarmSendFailedException(AppException):
    def __init__(self, message: str):
        self.message = message

    def __str__(self) -> str:
        return f"요청이 실패했습니다, ({self.message})"


class RateLimitException(AppException):
    def __str__(self) -> str:
        return "너무 많은 요청을 보내서 요청이 실패했습니다."
