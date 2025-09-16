import asyncio
import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator

import aiofiles
from aiopath import AsyncPath

from ..pydantic_models import Message, Role, SceneArchivingThread
from .message_broker import MessageBroker
from .exceptions import MessageBrokerError, MessageIsNotFoundError


@dataclass
class MessageNode:
    message: Message | None = None
    archive: Message | None = None


class FileMessageBroker(MessageBroker):

    def _build_fiesystem_cache(self, thread_uid: str | int) -> dict[int, MessageNode]:
        result: dict[int, MessageNode] = {}

        for f in self._storage_path.iterdir():
            if f.is_file() and f.name[:6].isdigit():
                order, *args, role_raw = f.name.split('_')
                int_order = int(order)
                role = Role(role_raw.split('.')[0])

                if role == Role.archive:
                    order_to, *_ = args
                    archive_for = [ o for o in range(int_order, int(order_to) + 1) ]
                else:
                    archive_for = None

                with open(f, 'r') as fopen:
                    message = Message(
                        thread_uid=thread_uid, order=int_order, role=Role(role), text=fopen.read(),
                        archive_for=archive_for
                    )
                    if role == Role.archive:
                        assert message.archive_for
                        for index in message.archive_for:
                            node = result.get(index, MessageNode())
                            node.archive = message
                            result[index] = node
                    else:
                        node = result.get(int_order, MessageNode())
                        node.message = message
                        result[int_order] = node
        return result

    def __init__(self, storage_path: Path) -> None:
        self._storage_path = storage_path
        self._filesystem_cache: dict[int, MessageNode] = self._build_fiesystem_cache('')
        return super().__init__()

    async def _get_message_from_file(self, thread_uid: str | int, filepath: Path) -> Message:
        order, *args, role = filepath.name.split('.')[0].split('_')
        int_order = int(order)

        if role == Role.archive:
            order_to, *_ = args
            archive_for = [ o for o in range(int_order, int(order_to) + 1) ]
        else:
            archive_for = None

        async with aiofiles.open(filepath, 'r') as fopen:
            return Message(
                thread_uid=thread_uid, order=int_order, role=Role(role), text=await fopen.read(),
                archive_for=archive_for
            )

    async def _get_iterator_for_message_pathfiles(self, thread_uid: str | int) -> AsyncIterator[Path]:
        async for f in AsyncPath(self._storage_path).iterdir():
            if await f.is_file() and f.name[:6].isdigit():
                yield Path(f)

    def _get_filepath_for_order_and_role(
        self, thread_uid: str | int, order: int, role: Role, order_to: int | None = None
    ) -> Path:
        if role != role.archive:
            return Path(self._storage_path / f'{order:06d}_{role.value}.txt')
        else:
            return Path(self._storage_path / f'{order:06d}_{order_to:06d}_{role.value}.txt')

    def _get_filepath_for_message(self, message: Message) -> Path:
        # if message.role == Role.archive and message.archive_for is None:
        #     raise MessageBrokerError("Trying to make archive message with null in 'archive_for'")

        return self._get_filepath_for_order_and_role(
            message.thread_uid, message.order, message.role,
            max(message.archive_for) if message.archive_for else None
        )

    async def _force_store_message(self, message: Message):
        async with aiofiles.open(self._get_filepath_for_message(message), 'w') as fopen:
            await fopen.write(message.text)

    async def get_messages_by_thread_uid(self, thread_uid: str | int) -> list[Message]:
        files = sorted(f for f in [ f async for f in self._get_iterator_for_message_pathfiles(thread_uid) ])
        return await asyncio.gather(*[ self._get_message_from_file(thread_uid, filepath) for filepath in files ])

    async def get_message_by_thread_uid_and_order(self, thread_uid: str | int, order: int) -> Message:
        if (order not in self._filesystem_cache):
            raise MessageIsNotFoundError(thread_uid, order, True)

        msg = self._filesystem_cache[order].message
        assert msg is not None
        return msg

        # for role in Role:
        #     if role == Role.archive:
        #         continue

        #     filepath = self._get_filepath_for_order_and_role(thread_uid, order, role)
        #     try:
        #         if await AsyncPath(filepath).exists():
        #             return await self._get_message_from_file(thread_uid, filepath)
        #     except PermissionError:
        #         pass

        # raise MessageIsNotFoundError(thread_uid, order)

    async def get_archive_by_thread_uid_and_order(self, thread_uid: str | int, order: int) -> Message:

        if (order not in self._filesystem_cache) or (self._filesystem_cache[order].archive is None):
            raise MessageIsNotFoundError(thread_uid, order, True)

        msg = self._filesystem_cache[order].archive
        assert msg is not None
        return msg

        # async for f in self._get_iterator_for_message_pathfiles(thread_uid):
        #     if f.name.startswith(f'{order:06d}') and f.name[:6].isdigit() and f.name[7:13].isdigit():
        #         filepath = self._get_filepath_for_order_and_role(thread_uid, order, Role.archive, int(f.name[7:13]))
        #         return await self._get_message_from_file(thread_uid, filepath)

        # raise MessageIsNotFoundError(thread_uid, order, True)

    async def get_thread_archiving_instruction(self, thread_uid: str | int) -> Message:
        async with aiofiles.open(self._storage_path / 'archiving_instruction.txt', 'r') as fopen:
            return Message(thread_uid=thread_uid, order=0, role=Role.system, text=await fopen.read())

    async def get_origin_thread(
        self, thread_uid: str | int, order_from: int = 0, order_to: int | None = None
    ) -> list[Message]:
        return [
            msg for msg in await self.get_messages_by_thread_uid(thread_uid)
                if msg.role != Role.archive and msg.order >= order_from and
                (order_to is None or msg.order <= order_to)
        ]

    async def get_thread_analysis_instruction(self, thread_uid: str | int) -> Message:
        async with aiofiles.open(self._storage_path / 'analysis_instruction.txt', 'r') as fopen:
            return Message(thread_uid=thread_uid, order=0, role=Role.system, text=await fopen.read())

    async def get_thread_hidden_context_creation_instruction(self, thread_uid: str | int) -> Message:
        async with aiofiles.open(self._storage_path / 'hidden_context_creation_instruction.txt', 'r') as fopen:
            return Message(thread_uid=thread_uid, order=0, role=Role.system, text=await fopen.read())

    async def get_thread_hidden_context_consistency_check_instruciton(self, thread_uid: str | int) -> Message:
        async with aiofiles.open(
            self._storage_path / 'hidden_context_consistency_check_instruction.txt', 'r'
        ) as fopen:
            return Message(thread_uid=thread_uid, order=0, role=Role.system, text=await fopen.read())

    async def store_hidden_context_message(self, hidden_context_message: Message) -> None:
        async with aiofiles.open(self._storage_path / 'hidden_context.txt', 'w') as fopen:
            await fopen.write(hidden_context_message.text)

    async def get_hidden_context_message(self, thread_uid: str | int) -> Message:
        async with aiofiles.open(self._storage_path / 'hidden_context.txt', 'r') as fopen:
            return Message(thread_uid=thread_uid, order=0, role=Role.hidden, text=await fopen.read())

    async def get_conversation_instruction(self, thread_uid: str | int) -> Message:
        async with aiofiles.open(self._storage_path / 'conversation_instruction.txt', 'r') as fopen:
            return Message(thread_uid=thread_uid, order=0, role=Role.system, text=await fopen.read())

    # async def compile_background(self, thread_uid: str | int, to_order: int) -> list[Message]:
    #     files = sorted(f for f in self._storage_path.iterdir() if f.is_file()
    #                         and f.name[:6].isdigit() and int(f.name[:6]) < to_order)

    #     return await asyncio.gather(*[ self._get_message_from_file(thread_uid, filepath) for filepath in files ])

    async def get_messages_by_orders_list(self, thread_uid: str | int, messages_orders: list[int]) -> list[Message]:
        files = sorted(f for f in self._storage_path.iterdir() if f.is_file()
                            and f.name[:6].isdigit() and int(f.name[:6]) in messages_orders)

        return await asyncio.gather(*[ self._get_message_from_file(thread_uid, filepath) for filepath in files ])

    async def set_archiving_message(self, archiving_message: Message) -> Message:

        msg_by_id_hash: dict[int, Message] = {}

        if archiving_message.archive_for is None:
            raise MessageBrokerError("Trying to make archive message with null in 'archive_for'")
        
        # check if message we archive exist
        for msg_id in archiving_message.archive_for:
            # if not, MessageIsNotFoundError is raised here
            msg_by_id_hash[msg_id] = await self.get_message_by_thread_uid_and_order(
                archiving_message.thread_uid, msg_id
            )

        await self._force_store_message(archiving_message)

        self._filesystem_cache = self._build_fiesystem_cache(archiving_message.thread_uid)

        return archiving_message

    async def compile_few_shot_thread_by_index(
        self, thread_uid: str | int, few_shots_index: int
    ) -> SceneArchivingThread:
        background: list[Message] = []

        try:
            for i in itertools.count(1):
                async with aiofiles.open(
                    self._storage_path / f'few_shots_background_{few_shots_index}_{i}.txt', 'r'
                ) as fopen:
                    background.append(Message(
                        thread_uid=thread_uid, order=0, role=Role.assistant, text=await fopen.read()
                    ))
        except FileNotFoundError:
            pass

        current_scene: list[Message] = []
        try:
            for i in itertools.count(1):
                async with aiofiles.open(
                    self._storage_path / f'few_shots_request_{few_shots_index}_{i}.txt', 'r'
                ) as fopen:
                    current_scene.append(Message(
                        thread_uid=thread_uid, order=0, role=Role.user, text=await fopen.read()
                    ))

                async with aiofiles.open(
                    self._storage_path / f'few_shots_response_{few_shots_index}_{i}.txt', 'r'
                ) as fopen:
                    current_scene.append(Message(
                        thread_uid=thread_uid, order=0, role=Role.assistant, text=await fopen.read()
                    ))
        except FileNotFoundError:
            pass

        async with aiofiles.open(
            self._storage_path / f'few_shots_archive_{few_shots_index}.txt', 'r'
        ) as fopen:
            return SceneArchivingThread(
                background=background,
                messages=current_scene,
                archive=Message(thread_uid=thread_uid, order=0, role=Role.archive, text=await fopen.read())
            )

    async def compile_few_shot_threads(self, thread_uid: str | int) -> list[SceneArchivingThread]:
        return [
            await self.compile_few_shot_thread_by_index(thread_uid, i) for i in range(1, 2)
            # TODO: check how much shots do i actually have
        ]

    async def add_message(self, message: Message) -> Message:

        if await AsyncPath(self._get_filepath_for_message(message)).exists():
            raise MessageBrokerError(f'Message with order {message.order} already exists')

        await self._force_store_message(message)
        self._filesystem_cache = self._build_fiesystem_cache(message.thread_uid)
        return message
