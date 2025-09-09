import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, TypedDict

from llm_toolkit.pydantic_models import Message, Role, SceneArchivingThread
from .exceptions import LLMAPIError


class _LLMMessage(TypedDict):
    role: Literal['system', 'user', 'assistant']
    content: str


class _LLMResponse(TypedDict):
    role: Literal['system', 'user', 'assistant']
    content: str


class LLMAPI(ABC):

    @classmethod
    def _compile_scene_thread(cls, scene_thread: SceneArchivingThread) -> list[_LLMMessage]:
        scene_background_thread = cls.join_messages_seq_to_gpt_msg(scene_thread.background, Role.user)
        current_scene_thread = cls.join_messages_seq_to_gpt_msg(scene_thread.messages, Role.user)

        result: list[_LLMMessage] = [
            {
                'role': Role.user.value,
                'content': ('=== BACKGROUND ===\n' + scene_background_thread['content'] +
                            '\n\n=== CURRENT SCENE ===\n' + current_scene_thread['content'])
            }
        ]
        if scene_thread.archive is not None:
            result.append(cls.msg_to_gpt_dict(scene_thread.archive))

        return result

    @abstractmethod
    async def get_archving_message(
        self, archiving_instruction: Message, archiving_thread: SceneArchivingThread,
        few_shots_threads: list[SceneArchivingThread] | None
    ) -> Message:
        """Generate archving message based on given instruciton message and background subthread with optional
           few-shots"""
        pass

    def _make_archiving_gpt_dicts_msgs(
        self, archiving_instruction: Message, archiving_thread: SceneArchivingThread,
        few_shots_threads: list[SceneArchivingThread] | None
    ) -> list[_LLMMessage]:
        archiving_openai_instruction_msg = self.msg_to_gpt_dict(archiving_instruction)

        few_shots_openai_msgs: list[_LLMMessage] = sum([
            self._compile_scene_thread(thread) for thread in few_shots_threads
        ], []) if few_shots_threads else []

        archving_openai_msgs = self._compile_scene_thread(archiving_thread)
        assert len(archving_openai_msgs) == 1, (
            'for some reason archiving thread in _make_archiving_gpt_dicts_msgs already has archive message'
        )

        return [ archiving_openai_instruction_msg ] + few_shots_openai_msgs + archving_openai_msgs

    @classmethod
    def msg_to_gpt_dict(cls, message: Message) -> _LLMMessage:
        role = Role.assistant if message.role == Role.archive else message.role
        if role not in (Role.assistant, Role.user, Role.system):
            raise LLMAPIError(f'Can not handle {message.role.value} role message by OpenAI API')

        return { 'role': role.value, 'content': message.text }

    @classmethod
    def join_messages_seq_to_gpt_msg(cls, messages: list[Message], role: Role) -> _LLMMessage:
        return {
            'role': role.value,
            'content': '\n\n'.join((cls.msg_to_gpt_dict(msg)['content'] for msg in messages))
        }
