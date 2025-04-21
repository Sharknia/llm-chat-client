import os
from collections.abc import Generator

from openai import OpenAI

from app.src.models.message import Message

from .base import LlmModels


class GrokModels(LlmModels):
    api_key = os.getenv("GROK_API_KEY", "null")
    base_url = "https://api.x.ai/v1"

    def __init__(self):
        # api key가 없는 경우 오류 발생
        if self.get_api_key() == "null":
            raise ValueError("GROK_API_KEY is not set")
        self.client = OpenAI(
            api_key=self.get_api_key(),
            base_url=self.base_url,
        )

    def get_api_key(self) -> str:
        return self.api_key

    def get_default_model_name(self) -> str:
        return "grok-3-latest"  # 기본 모델 이름 직접 반환

    def get_supported_models(self) -> list[str]:
        return [
            "grok-3-latest",
            "grok-3-mini-beta",
        ]

    def generate_completion_stream(
        self,
        messages: list[Message],
        model_name: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
    ) -> Generator[str, None, None]:
        # Grok은 OpenAI 형식을 따르므로 메시지를 dict로 변환
        formatted_messages = [msg.model_dump() for msg in messages]
        try:
            stream = self.client.chat.completions.create(
                model=model_name,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=True,
            )
            for chunk in stream:
                if (
                    chunk.choices
                    and chunk.choices[0].delta
                    and chunk.choices[0].delta.content
                ):
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"Grok API 호출 중 예외 발생: {e}")
            # 필요시 예외를 다시 발생시키거나 다른 방식으로 처리
            raise
