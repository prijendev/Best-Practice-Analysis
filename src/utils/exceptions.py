class BaseException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.message}"


class CloneRepositoryError(BaseException):
    pass


class InvalidSourceCodeLinkError(BaseException):
    pass


class InvalidLinkError(BaseException):
    pass


class NoPracticeFoundError(BaseException):
    pass


class BestPracticeProcessorError(BaseException):
    pass

