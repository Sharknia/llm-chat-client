import enum
import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv

# .env 파일의 환경 변수를 로드합니다.
load_dotenv()


class LLMModelListEnum(enum.Enum):
    GROK3_MINI_BETA = "grok-3-mini-beta"
    GROK3_LATEST = "grok-3-latest"
    GEMINI_1_5_PRO = "gemini-1.5-pro"

class LlmModels(ABC):
    @abstractmethod
    def get_api_key(self):
        pass

    @abstractmethod
    def get_model(
        self,
        model_enum: LLMModelListEnum = None,
    ):
        pass

    @abstractmethod
    def get_base_url(self):
        pass


class GrokModels(LlmModels):
    api_key = os.getenv("GROK_API_KEY", "null")
    model_enum = LLMModelListEnum
    base_url = "https://api.x.ai/v1"

    def get_api_key(self):
        return self.api_key

    def get_model(
        self,
        model_enum: LLMModelListEnum = model_enum.GROK3_MINI_BETA.value,
    ):
        return model_enum

    def get_base_url(self):
        return self.base_url


class GeminiModels(LlmModels):
    api_key = os.getenv("GEMINI_API_KEY", "null")
    model_enum = LLMModelListEnum
    base_url = "https://generativelanguage.googleapis.com/v1beta"

    def get_api_key(self):
        return self.api_key

    def get_model(
        self,
        model_enum: LLMModelListEnum = model_enum.GEMINI_1_5_PRO.value,
    ):
        return model_enum

    def get_base_url(self):
        return self.base_url
