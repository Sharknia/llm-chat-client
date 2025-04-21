from app.src.models.message import Message, RoleEnum

DEFAULT_SYSTEM_MESSAGE = None


class MessageList:
    def __init__(
        self,
        system_message: str = DEFAULT_SYSTEM_MESSAGE,
    ):
        # 기본 메시지를 초기화
        self.messages: list[Message] = []
        if system_message:
            self.addSystem(system_message)

    def addSystem(self, content: str) -> None:
        # 시스템 메시지를 추가
        self.messages.append(Message(role=RoleEnum.system, content=content))

    def addUser(self, content: str) -> None:
        # 사용자 메시지를 추가
        self.messages.append(Message(role=RoleEnum.user, content=content))

    def addAssistant(self, content: str) -> None:
        # 어시스턴트 메시지를 추가
        self.messages.append(Message(role=RoleEnum.assistant, content=content))

    def get_messages(self) -> list[Message]:
        # 구성된 메시지 리스트를 반환
        return self.messages
