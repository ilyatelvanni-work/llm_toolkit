import uuid

from llm_toolkit.pydantic_models import Message, Role

from .llm_api import LLMAPI

class MockLLMAPI(LLMAPI):

    async def get_archving_message(
        self, archiving_instruction: Message, background: list[Message], messages_to_archive: list[Message],
        few_shots: list[Message] | None = None
    ) -> Message:
        archive_for = [ msg.order for msg in messages_to_archive ]
        return Message(
            thread_uid=messages_to_archive[0].thread_uid, order=messages_to_archive[0].order,
            role=Role.archive, text=f'Some generated {uuid.uuid4()} for {archive_for}', archive_for=archive_for
        )