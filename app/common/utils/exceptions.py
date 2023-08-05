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
