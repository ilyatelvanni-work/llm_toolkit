from enum import StrEnum
from dataclasses import dataclass

from pydantic import BaseModel


class Role(StrEnum):
    assistant = 'assistant'
    user = 'user'
    system = 'system'
    archive = 'archive'
    hidden = 'hidden'


class Message(BaseModel):
    thread_uid: str | int
    order: int
    role: Role
    text: str
    archive_for: list[int] | None = None

    def __str__(self):
        if self.role == Role.hidden:
            return f'HIDDEN MESSAGE OF {self.thread_uid} thread'

        return super().__str__()


@dataclass
class SceneArchivingThread:
    background: list[Message]
    messages: list[Message]
    archive: Message | None = None
