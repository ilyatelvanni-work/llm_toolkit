import uuid

from llm_toolkit.pydantic_models import Message, Role, SceneArchivingThread

from .llm_api import LLMAPI

class MockLLMAPI(LLMAPI):

    async def get_archving_message(
        self, archiving_instruction: Message, archiving_thread: SceneArchivingThread,
        few_shots_threads: list[SceneArchivingThread] | None
    ) -> Message:
        archive_for = [ msg.order for msg in archiving_thread.messages ]

        print(f"{'=' * 40}")
        for msg in self._make_archiving_gpt_dicts_msgs(
            archiving_instruction, archiving_thread, few_shots_threads
        ):
            print(f"{'=' * 40}\n\nROLE: {msg['role']}")
            print(f"CONTENT: {msg['content']}\n\n")

        return Message(
            thread_uid=archiving_thread.messages[0].thread_uid, order=archiving_thread.messages[0].order,
            role=Role.archive, text=f'Some generated {uuid.uuid4()} for {archive_for}', archive_for=archive_for
        )
