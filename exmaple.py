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

message_list.addAssistant(
    content="""
안녕하세요! 무엇을 도와드릴까요? 궁금한 점이나 필요한 정보가 있으시면 언제든지 말씀해주세요. 😊
"""
)

message_list.addUser(
    content="""
뭘 도와줄 수 있는데요? 제 이름은 백엔드 개발자입니다. 
"""
)

message_list.addAssistant(
    content="""
안녕하세요, 백엔드 개발자님! 만나서 반갑습니다. 저는 다음과 같은 도움을 드릴 수 있습니다:

*   **정보 검색:** 궁금한 내용에 대해 검색하고, 관련 정보를 요약하거나 찾아드립니다.
*   **글쓰기:** 이메일, 편지, 에세이, 시 등 다양한 종류의 글을 작성하는 것을 도와드릴 수 있습니다. 초안 작성, 문장 개선, 문법 교정 등을 지원합니다.
*   **아이디어 구상:** 어떤 주제에 대해 아이디어를 떠올리는 것을 도와드릴 수 있습니다. 브레인스토밍, 마인드맵 작성 등을 통해 창의적인 생각을 촉진합니다.
*   **번역:** 간단한 문장이나 문단을 번역해 드립니다.
*   **요약:** 긴 텍스트를 짧고 간결하게 요약해 드립니다.
*   **질문 답변:** 다양한 분야에 대한 질문에 답해 드립니다.
*   **일상적인 대화:** 심심할 때 말벗이 되어 드리거나, 재미있는 이야기를 들려드릴 수도 있습니다.

이 외에도 제가 할 수 있는 일은 많습니다. 어떤 종류의 도움이 필요하신지 구체적으로 말씀해주시면, 최대한 도와드리겠습니다. 무엇을 도와드릴까요?
"""
)

message_list.addUser(
    content="""
아 제 이름이 뭐라고요?
"""
)


try:
    result = chat_client.get_completion_stream()
    for chunk in result:
        print(chunk, end="", flush=True)
    print()
except Exception as e:
    print(f"\n오류 발생: {e}")
