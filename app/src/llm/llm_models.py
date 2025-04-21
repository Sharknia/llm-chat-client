import enum
import os
from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any

from dotenv import load_dotenv
from google import genai
from openai import OpenAI

from app.src.models.message import Message, RoleEnum

# .env 파일의 환경 변수를 로드합니다.
load_dotenv()


class LLMModelListEnum(enum.Enum):
    GROK3_MINI_BETA = "grok-3-mini-beta"
    GROK3_LATEST = "grok-3-latest"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"


class LlmModels(ABC):
    @abstractmethod
    def get_api_key(self) -> str:
        pass

    @abstractmethod
    def get_default_model_name(self) -> str:
        pass

    @abstractmethod
    def generate_completion_stream(
        self,
        messages: list[Message],
        model_name: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        **kwargs: Any,  # 추가적인 모델별 파라미터
    ) -> Generator[str, None, None]:
        """메시지 리스트와 파라미터를 받아 API 호출 후 결과를 스트리밍으로 반환합니다."""
        pass


class GrokModels(LlmModels):
    api_key = os.getenv("GROK_API_KEY", "null")
    base_url = "https://api.x.ai/v1"
    default_model = LLMModelListEnum.GROK3_LATEST.value

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
        return self.default_model

    def generate_completion_stream(
        self,
        messages: list[Message],
        model_name: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        **kwargs: Any,
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
                **kwargs,  # Grok API에서 지원하는 다른 파라미터 (예: frequency_penalty)
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


class GeminiModels(LlmModels):
    api_key = os.getenv("GOOGLE_API_KEY", "null")
    default_model = LLMModelListEnum.GEMINI_2_0_FLASH.value

    def __init__(self):
        # api key가 없는 경우 오류 발생
        if self.get_api_key() == "null":
            raise ValueError("GOOGLE_API_KEY is not set")
        self.client = genai.Client(api_key=self.get_api_key())

    def get_api_key(self) -> str:
        return self.api_key

    def get_default_model_name(self) -> str:
        return self.default_model

    def _format_gemini_contents(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Gemini API의 'contents' 형식으로 변환합니다. system prompt는 제외합니다."""
        contents = []
        for msg in messages:
            if msg.role == RoleEnum.system:
                continue  # 시스템 메시지는 별도로 처리
            # 역할 매핑: assistant -> model, user -> user
            role = "model" if msg.role == RoleEnum.assistant else msg.role.value
            contents.append({"role": role, "parts": [{"text": msg.content}]})
        return contents

    def generate_completion_stream(
        self,
        messages: list[Message],
        model_name: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        # Extract system instruction
        system_instruction = None
        user_assistant_messages = []
        for msg in messages:
            if msg.role == RoleEnum.system:
                if system_instruction is None:  # 첫 번째 시스템 메시지 사용
                    system_instruction = msg.content
                else:
                    # 여러 시스템 메시지 처리 (필요시 연결 또는 오류 발생)
                    print(
                        "Warning: Multiple system messages found. Using the first one."
                    )
            else:
                user_assistant_messages.append(msg)

        # Gemini용 'contents' 포맷팅 (system 메시지 제외)
        gemini_contents = self._format_gemini_contents(user_assistant_messages)

        try:
            # client.models.generate_content_stream 호출 (system_instruction 제거)
            stream = self.client.models.generate_content_stream(
                model=model_name,
                contents=gemini_contents,
            )

            for chunk in stream:
                try:
                    if chunk.text:
                        yield chunk.text
                except ValueError:
                    # chunk.text가 없는 경우 오류 처리 (예: 안전 등급)
                    pass  # 텍스트 없는 청크 무시 (예: 안전 피드백)

        except Exception as e:
            print(f"Gemini API 호출 중 예외 발생: {e}")
            raise
