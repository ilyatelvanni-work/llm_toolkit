from ..message_broker import (
    MessageBrokerError,
    MessageIsNotFoundError as MessageBrokerMsgIsNotFoundError,
    ThreadIsNotFoundError as MessageBrokerThreadIsNotFoundError
)


def convert_message_broker_error_to_dialog_error(msg_broker_err: MessageBrokerError) -> 'DialogManagerError':
    if isinstance(msg_broker_err, MessageBrokerMsgIsNotFoundError):
        return MessageIsNotFoundError(msg_broker_err)
    elif isinstance(msg_broker_err, MessageBrokerThreadIsNotFoundError):
        return ThreadIsNotFoundError(msg_broker_err)
    else:
        raise Exception(f'{type(msg_broker_err)} message broker error has no handler in dialog manager converter')


class DialogManagerError(BaseException):
    def __init__(self, msg: str, status_code: int = 400):
        super().__init__(msg)
        self.status_code = status_code


class MessageIsNotFoundError(DialogManagerError):
    def __init__(self, msg_broker_err: MessageBrokerMsgIsNotFoundError):
        return super().__init__(str(msg_broker_err), 404)


class ThreadIsNotFoundError(DialogManagerError):
    def __init__(self, msg_broker_err: MessageBrokerThreadIsNotFoundError):
        return super().__init__(str(msg_broker_err), 404)
