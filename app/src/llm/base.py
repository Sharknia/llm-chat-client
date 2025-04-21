from abc import ABC, abstractmethod
from collections.abc import Generator

from app.src.models.message import Message


class LlmModels(ABC):
    @abstractmethod
    def get_api_key(self) -> str:
        pass

    @abstractmethod
    def get_default_model_name(self) -> str:
        pass

    @abstractmethod
    def get_supported_models(self) -> list[str]:
        """이 LLM 제공자가 지원하는 모델 이름 목록을 반환합니다."""
        pass

    @abstractmethod
    def generate_completion_stream(
        self,
        messages: list[Message],
        model_name: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
    ) -> Generator[str, None, None]:
        """메시지 리스트와 파라미터를 받아 API 호출 후 결과를 스트리밍으로 반환합니다."""
        pass
