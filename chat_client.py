from openai import OpenAI

from llm_models import LLMModelListEnum, LlmModels


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
        completion = self.client.chat.completions.create(
            model=self.llm_model_name, messages=self.messages
        )
        return completion.choices[0].message.content


# # Example usage
# if __name__ == "__main__":
#     model = GrokModels()
#     messages = [
#         {
#             "role": "system",
#             "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy."
#         },
#         {
#             "role": "user",
#             "content": "What is the meaning of life, the universe, and everything?"
#         },
#     ]

#     chat_client = ChatClient(model, model.grok2, messages)
#     print(chat_client.get_completion())
