from ..message_broker import MessageBroker
from ..pydantic_models import Message


class DialogManager:

    def __init__(self, message_broker: MessageBroker) -> None:
        self._message_broker = message_broker
        return super().__init__()

    async def create_thread(self, thread_uid: str | int) -> list[Message]:
        return await self._message_broker.get_messages_by_thread_uid(thread_uid)

    async def get_message_by_thread_uid_and_order(
        self, thread_uid: str | int, message_order: int
    ) -> Message:
        return await self._message_broker.get_message_by_thread_uid_and_order(thread_uid, message_order)

    async def get_thread_archiving_instruction(self, thread_uid: str | int) -> Message:
        return await self._message_broker.get_thread_archiving_instruction(thread_uid)

    async def compile_background(self, thread_uid: str | int, to_order: int) -> list[Message]:
        return await self._message_broker.compile_background(thread_uid, to_order)

    async def get_messages_by_orders_list(self, thread_uid: str | int, messages_orders: list[int]) -> list[Message]:
        return await self._message_broker.get_messages_by_orders_list(thread_uid, messages_orders)
