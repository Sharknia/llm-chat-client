from app.src.clients.chat_client import ChatClient
from app.src.llm.llm_models import GeminiModels
from app.src.models.message_list import MessageList

message_list = MessageList()

chat_client = ChatClient(
    llm_model=GeminiModels(),
    messages=message_list.get_messages(),
)

message_list.addUser(
    content="""
안녕하세요^^
"""
)

try:
    result = chat_client.get_completion_stream()
    for chunk in result:
        print(chunk, end="", flush=True)
    print()
except Exception as e:
    print(f"\n오류 발생: {e}")
