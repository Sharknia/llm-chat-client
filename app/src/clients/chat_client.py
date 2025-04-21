from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion

from app.src.llm.llm_models import LLMModelListEnum, LlmModels


class ChatClient:
    def __init__(
        self,
        llm_model: LlmModels,
        messages: list,
        llm_model_name: LLMModelListEnum = LLMModelListEnum.GROK3_LATEST.value,
    ):
        self.llm_model = llm_model
        self.llm_model_name = llm_model.get_model(llm_model_name)
        self.messages = messages
        self.client = OpenAI(
            api_key=llm_model.get_api_key(),
            base_url=llm_model.get_base_url(),
        )

    def get_completion(self):
        try:
            completion: ChatCompletion = self.client.chat.completions.create(
                model=self.llm_model_name,
                messages=self.messages,
                temperature=1.0,
                max_tokens=2500,
                top_p=0.95,
                stream=True,
            )
            for chunk in completion:
                if chunk.choices[0].finish_reason == "stop":
                    break
                if chunk.choices[0].delta.content is not None:
                    print(chunk.choices[0].delta.content, end="", flush=True)
        except Exception as e:
            return f"예외가 발생했습니다: {e}"
