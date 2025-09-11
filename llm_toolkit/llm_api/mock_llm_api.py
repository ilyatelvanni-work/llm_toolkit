import uuid

from llm_toolkit.pydantic_models import Message, Role, SceneArchivingThread

from .llm_api import _LLMMessage, HiddenContextConsistencyCheckResult, LLMAPI


class MockLLMAPI(LLMAPI):

    def count_single_message_tokens(self, msg: Message) -> int:
        return 12

    @staticmethod
    def print_msg(msg: _LLMMessage) -> None:
        print(f"{'=' * 40}\n\nROLE: {msg['role']}")
        print(f"CONTENT: {msg['content']}\n\n")

    @staticmethod
    def print_text(text: str) -> None:
        print(text)

    async def get_archving_message(
        self, archiving_instruction: Message, archiving_thread: SceneArchivingThread,
        few_shots_threads: list[SceneArchivingThread] | None
    ) -> Message:
        archive_for = [ msg.order for msg in archiving_thread.messages ]

        self.print_text(f"{'=' * 40}")
        for msg in self._make_archiving_gpt_dicts_msgs(
            archiving_instruction, archiving_thread, few_shots_threads
        ):
            self.print_msg(msg)

        return Message(
            thread_uid=archiving_thread.messages[0].thread_uid, order=archiving_thread.messages[0].order,
            role=Role.archive, text=f'Some generated {uuid.uuid4()} for {archive_for}', archive_for=archive_for
        )

    async def get_thread_response(self, thread: list[Message]) -> Message:

        self.print_text(f"{'=' * 40}")
        for msg in self.convert_thread_into_llm_msgs(thread):
            self.print_msg(msg)

        return Message(
            thread_uid=thread[0].thread_uid, order=thread[0].order,
            role=Role.archive, text=f'Some generated {uuid.uuid4()} for thread'
        )

    async def make_hidden_context_message(
        self, hidden_context_creation_instruction: Message, thread: list[Message], context_message: Message
    ) -> Message:

        self.print_text(f"{'=' * 40}")
        for msg in self._make_hidden_context_creation_gpt_msgs(
            hidden_context_creation_instruction, thread, context_message
        ):
            self.print_msg(msg)

        return Message(
            thread_uid=context_message.thread_uid, order=0,
            role=Role.hidden, text=f'Some generated HIDDEN {uuid.uuid4()} for thread'
        )

    async def make_hidden_context_check(
        self, hidden_context_consistency_check_instruciton: Message, current_thread: list[Message],
        hidden_context: Message
    ) -> HiddenContextConsistencyCheckResult:

        self.print_text(f"{'=' * 40}")
        for msg in self._make_hidden_context_consistancy_check_gpt_msgs(
            hidden_context_consistency_check_instruciton, current_thread, hidden_context
        ):
            self.print_msg(msg)

        return HiddenContextConsistencyCheckResult(
            consistency_score=0.85, hook_alignment_score=0.58, logical_coherence_score = 0.92,
            token_efficiency_score=0.69
        )
