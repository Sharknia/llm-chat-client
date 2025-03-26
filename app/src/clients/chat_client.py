from openai import OpenAI

from app.src.llm.llm_models import LLMModelListEnum, LlmModels


class ChatClient:
    def __init__(
        self,
        llm_model: LlmModels,
        messages: list,
        llm_model_name: LLMModelListEnum = None,
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
            completion = self.client.chat.completions.create(
                model=self.llm_model_name,
                messages=self.messages,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print("예외가 발생했습니다:", e)
            return f"예외가 발생했습니다: {e}"
