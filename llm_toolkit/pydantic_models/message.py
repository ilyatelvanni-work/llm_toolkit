from enum import StrEnum

from pydantic import BaseModel


class Role(StrEnum):
    assistant = 'assistant'
    user = 'user'
    system = 'system'


class Message(BaseModel):
    thread_uid: str | int
    order: int
    role: Role
    text: str
