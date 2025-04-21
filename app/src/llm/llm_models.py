import enum
import os
from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any

from dotenv import load_dotenv
from google import genai
from openai import OpenAI  # OpenAI 라이브러리 임포트

from app.src.models.message import Message, RoleEnum  # Message와 RoleEnum 임포트

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
    api_key = os.getenv("GEMINI_API_KEY", "null")
    # Default model updated based on user example
    default_model = LLMModelListEnum.GEMINI_2_0_FLASH.value

    def __init__(self):
        # Client initialization remains the same
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
                continue  # System message is handled separately
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
                if system_instruction is None:  # Use the first system message
                    system_instruction = msg.content
                else:
                    # Handle multiple system messages if necessary, e.g., concatenate or raise error
                    print(
                        "Warning: Multiple system messages found. Using the first one."
                    )
            else:
                user_assistant_messages.append(msg)

        # Gemini용 'contents' 포맷팅 (system 메시지 제외)
        gemini_contents = self._format_gemini_contents(user_assistant_messages)

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "top_p": top_p,
            **kwargs.get("generation_config", {}),
        }
        safety_settings = kwargs.get("safety_settings")

        try:
            # Use the model name directly as per the example
            stream = self.client.models.generate_content_stream(
                model=model_name,  # Removed 'models/' prefix
                contents=gemini_contents,
                system_instruction=system_instruction,  # Pass system instruction
                generation_config=generation_config,
                safety_settings=safety_settings,
            )

            for chunk in stream:
                try:
                    if chunk.text:
                        yield chunk.text
                except ValueError:
                    # Handles potential errors if chunk.text doesn't exist (e.g., safety ratings)
                    pass  # Ignore chunks without text (like safety feedback)

        except Exception as e:
            print(f"Gemini API 호출 중 예외 발생: {e}")
            raise
