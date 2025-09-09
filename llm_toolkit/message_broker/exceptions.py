class MessageBrokerError(BaseException):
    pass


class MessageIsNotFoundError(MessageBrokerError):
    def __init__(self, thread_uid: str | int, order: int, archive: bool = False):
        return super().__init__(f"There's no {'archive ' if archive else ''}{order} message in {thread_uid} thread")


class ThreadIsNotFoundError(MessageBrokerError):
    def __init__(self, thread_uid: str | int):
        return super().__init__(f"There's no {thread_uid} thread")
