from abc import ABC, abstractmethod

from ..pydantic_models import Message


class MessageBroker(ABC):

    @abstractmethod
    async def get_messages_by_thread_uid(self, thread_uid: str | int) -> list[Message]:
        """Return all messages in the thread."""
        pass

    @abstractmethod
    async def get_message_by_thread_uid_and_order(
        self, thread_uid: str | int, message_order: int
    ) -> Message:
        pass

    @abstractmethod
    async def get_thread_archiving_instruction(self, thread_uid: str | int) -> Message:
        pass
