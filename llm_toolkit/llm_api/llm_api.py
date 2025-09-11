import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, cast, ClassVar, Literal, TypedDict

from llm_toolkit.pydantic_models import Message, Role, SceneArchivingThread
from .exceptions import LLMAPIError


LLMAPIRole = Literal['system', 'user', 'assistant']


class _LLMMessage(TypedDict):
    role: LLMAPIRole
    content: str


class _LLMResponse(TypedDict):
    role: LLMAPIRole
    content: str


@dataclass
class HiddenContextConsistencyCheckResult:
    consistency_score: float
    hook_alignment_score: float
    logical_coherence_score: float
    token_efficiency_score: float

    json_schema: ClassVar[dict[str, Any]] = {
        "type": "json_schema",
        "json_schema": {
            "name": "check_hidden_context_result",
            "schema": {
                "type": "object",
                "properties": {
                    "consistency_score": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
                    "hook_alignment_score": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
                    "logical_coherence_score": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
                    "token_efficiency_score": { "type": "number", "minimum": 0.0, "maximum": 1.0 }
                },
                "required": [
                    "consistency_score", "hook_alignment_score", "logical_coherence_score", "token_efficiency_score"
                ]
            }
        }
    }


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
    def count_single_message_tokens(self, msg: Message) -> int:
        pass

    @abstractmethod
    async def get_archving_message(
        self, archiving_instruction: Message, archiving_thread: SceneArchivingThread,
        few_shots_threads: list[SceneArchivingThread] | None
    ) -> Message:
        """Generate archving message based on given instruciton message and background subthread with optional
           few-shots"""
        pass

    @abstractmethod
    async def get_thread_response(self, thread: list[Message]) -> Message:
        pass

    @abstractmethod
    async def make_hidden_context_message(
        self, hidden_context_creation_instruction: Message, thread: list[Message], context_message: Message
    ) -> Message:
        pass

    def convert_thread_into_llm_msgs(self, thread: list[Message]) -> list[_LLMMessage]:
        return [ self.msg_to_gpt_dict(msg) for msg in thread ]

    @classmethod
    def _make_archiving_gpt_dicts_msgs(
        cls, archiving_instruction: Message, archiving_thread: SceneArchivingThread,
        few_shots_threads: list[SceneArchivingThread] | None
    ) -> list[_LLMMessage]:
        archiving_openai_instruction_msg = cls.msg_to_gpt_dict(archiving_instruction)

        few_shots_openai_msgs: list[_LLMMessage] = sum([
            cls._compile_scene_thread(thread) for thread in few_shots_threads
        ], []) if few_shots_threads else []

        archving_openai_msgs = cls._compile_scene_thread(archiving_thread)
        assert len(archving_openai_msgs) == 1, (
            'for some reason archiving thread in _make_archiving_gpt_dicts_msgs already has archive message'
        )

        return [ archiving_openai_instruction_msg ] + few_shots_openai_msgs + archving_openai_msgs

    @classmethod
    def _make_hidden_context_creation_gpt_msgs(
        cls, hidden_context_creation_instruction: Message, thread: list[Message], context_message: Message
    ) -> list[_LLMMessage]:
        hidden_context_creation_instruction_msg = cls.msg_to_gpt_dict(hidden_context_creation_instruction)
        thread_llm_msg = cls.join_messages_seq_to_gpt_msg(thread, Role.user)
        thread_llm_msg['content'] = '=== BACKGROUND ===\n\n' + thread_llm_msg['content']
        context_llm_msg = cls.msg_to_gpt_dict(context_message)
        context_llm_msg['role'] = 'user'
        context_llm_msg['content'] = '=== CURRENT QUEST LINE ===\n\n' + context_llm_msg['content']

        return [ hidden_context_creation_instruction_msg, thread_llm_msg, context_llm_msg ]

    @classmethod
    def msg_to_gpt_dict(cls, message: Message, role: Role | None = None, prefix: str = '') -> _LLMMessage:
        role = role or (Role.user if message.role == Role.archive else message.role)
        if role not in (Role.assistant, Role.user, Role.system):
            raise LLMAPIError(f'Can not handle {message.role.value} role message by OpenAI API')

        return { 'role': cast(LLMAPIRole, role.value), 'content': prefix + message.text }

    @classmethod
    def join_messages_seq_to_gpt_msg(cls, messages: list[Message], role: Role, prefix: str = '') -> _LLMMessage:
        return {
            'role': cast(LLMAPIRole, role.value),
            'content': prefix + ('\n\n'.join((cls.msg_to_gpt_dict(msg)['content'] for msg in messages)))
        }

    @abstractmethod
    async def make_hidden_context_check(
        self, hidden_context_consistency_check_instruciton: Message, current_thread: list[Message],
        hidden_context: Message
    ) -> HiddenContextConsistencyCheckResult:
        pass

    @classmethod
    def _make_hidden_context_consistancy_check_gpt_msgs(
        cls, hidden_context_consistency_check_instruciton: Message, current_thread: list[Message],
        hidden_context: Message
    ) -> list[_LLMMessage]:

        hidden_context_consistency_check_instruciton_msg = cls.msg_to_gpt_dict(
            hidden_context_consistency_check_instruciton
        )
        thread_llm_msg = cls.join_messages_seq_to_gpt_msg(current_thread, Role.user, prefix = '=== BACKGROUND ===\n\n')
        hidden_context_msg = cls.msg_to_gpt_dict(hidden_context, Role.user, prefix = '=== QUEST SUMMARING ===\n\n')

        return [ hidden_context_consistency_check_instruciton_msg, thread_llm_msg, hidden_context_msg ]
