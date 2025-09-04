from pathlib import Path

from ..pydantic_models import Message, Role
from .message_broker import MessageBroker


class FileMessageBroker(MessageBroker):

    def __init__(self, storage_path: Path) -> None:
        self._storage_path = storage_path
        return super().__init__()

    async def get_messages_by_thread_uid(self, thread_uid: str | int) -> list[Message]:

        files = sorted(f for f in self._storage_path.iterdir() if f.is_file() and f.name[:6].isdigit())

        messages = []
        for filepath in files:
            order, role = filepath.name.split('.')[0].split('_')
            int_order = int(order)
            with open(filepath, 'r') as fopen:
                messages.append(
                    Message(thread_uid=thread_uid, order=int_order, role=Role(role), text=fopen.read())
                )

        return messages

    async def get_message_by_thread_uid_and_order(
        self, thread_uid: str | int, message_order: int
    ) -> Message:
        filepath = next(
            (   f for f in self._storage_path.iterdir() if f.is_file() and
                f.name.startswith(f'{message_order:06d}')
            ), None
        )

        if filepath is None:
            raise IndexError(f"There's no {message_order} message in {thread_uid} thread")

        _, role = filepath.name.split('.')[0].split('_')

        with open(filepath, 'r') as fopen:
            return Message(thread_uid=thread_uid, order=message_order, role=Role(role), text=fopen.read())

    async def get_thread_archiving_instruction(self, thread_uid: str | int) -> Message:
        with open(self._storage_path / 'archiving_instruction.txt') as fopen:
            return Message(thread_uid=thread_uid, order=0, role=Role.system, text=fopen.read())
