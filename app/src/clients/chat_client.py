from collections.abc import Generator
from typing import Any

from app.src.llm.llm_models import LlmModels
from app.src.models.message import Message


class ChatClient:
    def __init__(
        self,
        llm_model: LlmModels,
        messages: list[Message],
        model_name: str | None = None,
    ):
        self.llm_model = llm_model
        self.model_name = model_name or llm_model.get_default_model_name()
        self.messages = messages

    def get_completion_stream(
        self,
        temperature: float = 1.0,
        max_tokens: int = 2500,
        top_p: float = 0.95,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """LLM 모델 객체에 스트리밍 생성을 위임하고 결과를 yield합니다."""
        try:
            stream = self.llm_model.generate_completion_stream(
                messages=self.messages,
                model_name=self.model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                **kwargs,
            )
            yield from stream

        except Exception as e:
            print(f"ChatClient에서 스트림 처리 중 예외 발생: {e}")
            raise
