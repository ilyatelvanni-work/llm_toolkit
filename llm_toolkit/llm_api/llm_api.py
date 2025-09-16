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
    consistency_with_background: float
    logical_coherence: float
    hook_alignment: float
    mechanism_specificity: float
    proof_sufficiency: float
    scope_containment: float
    difficulty_appropriateness: float
    ambiguity_control: float
    dryness_and_efficiency: float
    temporal_and_spatial_clarity: float
    verifiability_in_play: float

    json_schema: ClassVar[dict[str, Any]] = {
        "type": "json_schema",
        "json_schema": {
            "name": "check_hidden_context_result",
            "schema": {
                "type": "object",
                "properties": {
                    "consistency_with_background": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
                    "logical_coherence": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
                    "hook_alignment": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
                    "mechanism_specificity": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
                    "proof_sufficiency": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
                    "scope_containment": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
                    "difficulty_appropriateness": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
                    "ambiguity_control": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
                    "dryness_and_efficiency": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
                    "temporal_and_spatial_clarity": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
                    "verifiability_in_play": { "type": "number", "minimum": 0.0, "maximum": 1.0 }
                },
                "required": [
                    "consistency_with_background", "logical_coherence", "hook_alignment", "mechanism_specificity",
                    "proof_sufficiency", "scope_containment", "difficulty_appropriateness", "ambiguity_control",
                    "dryness_and_efficiency", "temporal_and_spatial_clarity", "verifiability_in_play"
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

    @abstractmethod
    async def make_conversation_continuation_message(
        self, narration_instruction: Message, hidden_context: Message, archive_subthread: list[Message],
        conversation_subthread: list[Message]
    ) -> Message:
        pass

    @classmethod
    def _make_conversation_continuation_gpt_msgs(
        cls, narration_instruction: Message, hidden_context: Message, archive_subthread: list[Message],
        conversation_subthread: list[Message]
    ) -> list[_LLMMessage]:
        conversation_instruction_msg = cls.msg_to_gpt_dict(narration_instruction)
        conversation_instruction_msg['content'] += '\n\n=== CURRENT QUEST ===\n\n' + hidden_context.text
        archive_msg = cls.join_messages_seq_to_gpt_msg(archive_subthread, Role.user, '=== ARCHIVE ===\n\n')
        conversation_msgs = [ cls.msg_to_gpt_dict(msg) for msg in conversation_subthread ]
        return [ conversation_instruction_msg ] + [ archive_msg ] + conversation_msgs
