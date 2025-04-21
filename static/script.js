// WebSocket 연결 및 메시지 처리는 나중에 추가됩니다.
function sendMessage() {
    const messageInput = document.getElementById('message');
    const message = messageInput.value.trim();
    if (message) {
        // 임시로 사용자 메시지를 채팅창에 표시 (나중에 WebSocket으로 처리)
        const chatbox = document.getElementById('chatbox');
        const userDiv = document.createElement('div');
        userDiv.classList.add('message', 'user-message');
        userDiv.textContent = message;
        chatbox.appendChild(userDiv);
        chatbox.scrollTop = chatbox.scrollHeight; // 스크롤 맨 아래로

        messageInput.value = ''; // 입력창 비우기

        // TODO: WebSocket을 통해 서버로 메시지 전송 로직 추가
        console.log('Sending message (via WebSocket later):', message);
    }
}

// Enter 키로 메시지 전송
document.getElementById('message').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// TODO: WebSocket 연결 및 서버로부터 메시지 수신 로직 추가
console.log('WebSocket connection logic to be added here.');
