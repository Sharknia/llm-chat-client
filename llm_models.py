import enum
import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv

# .env 파일의 환경 변수를 로드합니다.
load_dotenv()


class LLMModelListEnum(enum.Enum):
    GROK2_VISION_1212 = "grok-2-vision-1212"
    GROK2_1212 = "grok-2-1212"


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
        model_enum: LLMModelListEnum = None,
    ):
        if model_enum is None:
            model_enum = self.model_enum.GROK2_1212
        return model_enum.value

    def get_base_url(self):
        return self.base_url
