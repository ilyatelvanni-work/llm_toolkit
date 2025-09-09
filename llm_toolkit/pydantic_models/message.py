from enum import StrEnum
from dataclasses import dataclass

from pydantic import BaseModel


class Role(StrEnum):
    assistant = 'assistant'
    user = 'user'
    system = 'system'
    archive = 'archive'


class Message(BaseModel):
    thread_uid: str | int
    order: int
    role: Role
    text: str
    archive_for: list[int] | None = None


@dataclass
class SceneArchivingThread:
    background: list[Message]
    messages: list[Message]
    archive: Message | None = None
