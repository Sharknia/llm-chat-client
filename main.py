from chat_client import ChatClient
from llm_models import GrokModels

messages = [
    {
        "role": "system",
        "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy.",
    },
    {
        "role": "user",
        "content": "What is the meaning of life, the universe, and everything?",
    },
]

chat_client = ChatClient(
    llm_model=GrokModels(),
    messages=messages,
)
result = chat_client.get_completion()
print(result)
