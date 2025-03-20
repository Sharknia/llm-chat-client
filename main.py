from chat_client import ChatClient
from llm_models import GrokModels
from message_list import MessageList

message_list = MessageList()

chat_client = ChatClient(
    llm_model=GrokModels(),
    messages=message_list.get_messages(),
)

result = chat_client.get_completion()
print(result)
