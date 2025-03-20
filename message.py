from enum import Enum

from pydantic import BaseModel


class RoleEnum(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"


class Message(BaseModel):
    role: RoleEnum
    content: str


# 사용 예시
messages = [
    Message(
        role=RoleEnum.system,
        content="You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy.",
    ),
    Message(
        role=RoleEnum.user,
        content="What is the meaning of life, the universe, and everything?",
    ),
    Message(role=RoleEnum.assistant, content="42"),
]
