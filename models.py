from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv

# .env 파일의 환경 변수를 로드합니다.
load_dotenv()

class Models(ABC):
    @abstractmethod
    def get_api_key(self):
        pass

class GrokModels(Models):
    api_key = os.getenv('GROK_API_KEY', 'null')
    grok2 = "grok-2-1212"

    def get_api_key(self):
        return self.api_key

class ChatGPTModels(Models):
    api_key = os.getenv('CHATGPT_API_KEY', 'null')
    chatgpt_3_5 = "chatgpt-3.5"
    chatgpt_4 = "chatgpt-4"

    def get_api_key(self):
        return self.api_key