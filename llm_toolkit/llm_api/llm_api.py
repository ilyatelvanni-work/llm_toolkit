from abc import ABC, abstractmethod

from llm_toolkit.pydantic_models import Message


class LLMAPI(ABC):

    @abstractmethod
    async def get_archving_message(
        self, archiving_instruction: Message, background: list[Message], messages_to_archive: list[Message],
        few_shots: list[Message] | None = None
    ) -> Message:
        """Generate archving message based on given instruciton message and background subthread with optional
           few-shots"""
        pass
