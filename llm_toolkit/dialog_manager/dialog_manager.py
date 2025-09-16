import asyncio

from llm_toolkit.pydantic_models import Message, Role, SceneArchivingThread
from llm_toolkit.message_broker import (
    MessageBroker, MessageBrokerError, MessageIsNotFoundError as MessageBrokerMsgIsNotFoundError
)
from .exceptions import convert_message_broker_error_to_dialog_error


class DialogManager:

    def __init__(self, message_broker: MessageBroker) -> None:
        self._message_broker = message_broker
        return super().__init__()

    async def create_thread(self, thread_uid: str | int) -> list[Message]:
        return await self._message_broker.get_messages_by_thread_uid(thread_uid)

    async def get_message_by_thread_uid_and_order(self, thread_uid: str | int, message_order: int) -> Message:
        try:
            return await self._message_broker.get_message_by_thread_uid_and_order(thread_uid, message_order)
        except MessageBrokerError as err:
            raise convert_message_broker_error_to_dialog_error(err)

    async def get_thread_archiving_instruction(self, thread_uid: str | int) -> Message:
        return await self._message_broker.get_thread_archiving_instruction(thread_uid)

    async def compile_few_shot_threads(self, thread_uid: str | int) -> list[SceneArchivingThread]:
        return await self._message_broker.compile_few_shot_threads(thread_uid)

    async def compile_current_scene_thread(
        self, thread_uid: str | int, current_scene_orders: list[int]
    ) -> SceneArchivingThread:
        background = await self.compile_background(thread_uid, min(current_scene_orders))
        current_scene = await self.get_messages_by_orders_list(thread_uid, current_scene_orders)
        return SceneArchivingThread(background=background, messages=current_scene, archive=None)

    async def compile_background(self, thread_uid: str | int, to_order: int) -> list[Message]:
        return [ msg for msg in (await self.compile_and_get_thread(thread_uid)) if msg.order < to_order ]

    async def get_messages_by_orders_list(self, thread_uid: str | int, messages_orders: list[int]) -> list[Message]:
        return [ msg for msg in (
            await self._message_broker.get_messages_by_orders_list(thread_uid, messages_orders)
        ) if msg.role != Role.archive ]

    async def _compile_message_by_thread_uid_and_order(
        self, thread_uid: str | int, order: int
    ) -> Message | None:
        try:
            return await self._message_broker.get_archive_by_thread_uid_and_order(thread_uid, order)
        except MessageBrokerMsgIsNotFoundError:
            try:
                return await self._message_broker.get_message_by_thread_uid_and_order(thread_uid, order)
            except MessageBrokerMsgIsNotFoundError:
                return None

    async def compile_and_get_thread(self, thread_uid: str | int) -> list[Message]:

        compiled_messages: dict[int, Message] = {}
        order = 0
        async def generate():
            nonlocal compiled_messages
            nonlocal thread_uid
            nonlocal order

            loc_order = order
            order += 1

            compiled_message = await self._compile_message_by_thread_uid_and_order(thread_uid, loc_order)
            if compiled_message is not None:
                compiled_messages[loc_order] = compiled_message
                await generate()

        await asyncio.gather(*[ generate() for _ in range(30) ])

        order = 0
        thread: list[Message] = []
        while ((order := order + 1) <= max(compiled_messages.keys())):
            message = compiled_messages[order]
            thread.append(message)
            if message.role == Role.archive:
                assert message.archive_for
                order = max(message.archive_for)

        return thread

    async def get_thread_analysis_instruction(self, thread_uid: str | int) -> Message:
        return await self._message_broker.get_thread_analysis_instruction(thread_uid)

    async def get_origin_thread(
        self, thread_uid: str | int, order_from: int = 0, order_to: int | None = None
    ) -> list[Message]:
        return await self._message_broker.get_origin_thread(thread_uid, order_from, order_to)

    async def get_thread_hidden_context_creation_instruction(self, thread_uid: str | int) -> Message:
        return await self._message_broker.get_thread_hidden_context_creation_instruction(thread_uid)

    async def get_thread_hidden_context_consistency_check_instruciton(self, thread_uid: str | int) -> Message:
        return await self._message_broker.get_thread_hidden_context_consistency_check_instruciton(thread_uid)

    async def get_hidden_context_message(self, thread_uid: str | int) -> Message:
        return await self._message_broker.get_hidden_context_message(thread_uid)

    async def add_message(self, message: Message) -> Message:
        return await self._message_broker.add_message(message)

    async def get_conversation_instruction(self, thread_uid: str | int) -> Message:
        return await self._message_broker.get_conversation_instruction(thread_uid)
