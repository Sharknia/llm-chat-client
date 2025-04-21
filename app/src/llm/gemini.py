import os
from collections.abc import Generator
from typing import Any

from google import genai
from google.genai import types

from app.src.models.message import Message, RoleEnum

from .base import LlmModels


class GeminiModels(LlmModels):
    api_key = os.getenv("GOOGLE_API_KEY", "null")

    def __init__(self):
        # api key가 없는 경우 오류 발생
        if self.get_api_key() == "null":
            raise ValueError("GOOGLE_API_KEY is not set")
        self.client = genai.Client(api_key=self.get_api_key())

    def get_api_key(self) -> str:
        return self.api_key

    def get_default_model_name(self) -> str:
        return "gemini-2.5-flash-preview-04-17"  # 기본 모델 이름 직접 반환

    def get_supported_models(self) -> list[str]:
        return [
            "gemini-2.5-flash-preview-04-17",
            "gemini-2.0-flash",
        ]

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

    def _extract_system_instruction(self, messages: list[Message]) -> str | None:
        """메시지 목록에서 모든 시스템 명령어 내용을 추출하여 합칩니다."""
        system_instructions = []
        for msg in messages:
            if msg.role == RoleEnum.system:
                system_instructions.append(msg.content)

        if not system_instructions:
            return None

        # 시스템 메시지 내용을 줄 바꿈 두 개로 합침
        return "\n\n".join(system_instructions)

    def generate_completion_stream(
        self,
        messages: list[Message],
        model_name: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
    ) -> Generator[str, None, None]:
        # 시스템 명령어 추출 및 사용자/어시스턴트 메시지 분리
        system_instruction = self._extract_system_instruction(messages)
        user_assistant_messages = [
            msg for msg in messages if msg.role != RoleEnum.system
        ]

        # Gemini용 'contents' 포맷팅 (시스템 메시지 제외된 리스트 사용)
        gemini_contents = self._format_gemini_contents(user_assistant_messages)

        try:
            # config 생성 시 추출된 system_instruction 사용
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=max_tokens,
                temperature=temperature,
                topP=top_p,
            )

            stream = self.client.models.generate_content_stream(
                model=model_name,
                contents=gemini_contents,
                config=config,
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
