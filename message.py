from enum import Enum

from pydantic import BaseModel


class RoleEnum(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"


class Message(BaseModel):
    role: RoleEnum
    content: str
