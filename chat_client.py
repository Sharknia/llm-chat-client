from openai import OpenAI

from llm_models import Models


class ChatClient:
    def __init__(self, model: Models, model_name: str, messages: list):
        self.model = model
        self.model_name = model_name
        self.messages = messages
        self.client = OpenAI(
            api_key=model.get_api_key(),
            base_url=model.get_base_url(),
        )

    def get_completion(self):
        completion = self.client.chat.completions.create(
            model=self.model_name, messages=self.messages
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
