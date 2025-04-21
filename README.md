# LLM Chat Client (grok-crobat)

다양한 LLM 모델(현재 Grok 및 Gemini 지원)과 상호작용할 수 있는 간단한 Python 채팅 클라이언트입니다.

## 주요 기능

-   Grok 및 Google Gemini 모델 지원 (확장 가능)
-   스트리밍 방식으로 LLM 응답 처리
-   FastAPI를 사용한 간단한 웹 서버 (현재는 기본 루트만 존재)
-   Poetry를 사용한 의존성 관리

## 설정

1.  **저장소 클론:**

    ```bash
    git clone https://github.com/Sharknia/llm-chat-client.git
    cd llm-chat-client
    ```

2.  **Poetry 설치:** (이미 설치되어 있지 않다면)

    ```bash
    pip install poetry
    ```

    또는 [공식 문서](https://python-poetry.org/docs/#installation) 참조

3.  **의존성 설치:**

    ```bash
    poetry install
    ```

4.  **환경 변수 설정:**
    프로젝트 루트에 `.env` 파일을 생성하고 다음 환경 변수들을 설정합니다.
    (실제 운영 환경에서는 안전한 비밀번호를 사용하고 API 키를 입력하세요.)

    ```dotenv
    # .env 예시

    # PostgreSQL 설정 (docker-compose.yml 참조)
    POSTGRES_USER=user
    POSTGRES_PASSWORD=password
    POSTGRES_DB=llm_chat_db

    # FastAPI에서 사용할 DB URL
    DATABASE_URL=postgresql://user:password@db:5432/llm_chat_db

    # LLM API 키
    GROK_API_KEY=your_grok_api_key_here
    GOOGLE_API_KEY=your_google_api_key_here
    ```

## 사용법

### Docker Compose를 사용한 개발 환경 실행 (권장)

Docker와 Docker Compose가 설치되어 있어야 합니다.

1.  **`.env` 파일 생성 및 설정:** 위의 "환경 변수 설정" 섹션을 참조하여 `.env` 파일을 생성하고 필요한 값을 입력합니다.
2.  **서비스 실행:** 다음 명령어를 실행하면 PostgreSQL 데이터베이스와 FastAPI 웹 서버가 함께 빌드되고 실행됩니다.

    ```bash
    make dev
    ```

    또는 직접 Docker Compose 명령어를 사용할 수 있습니다:

    ```bash
    docker compose up --build
    ```

    애플리케이션은 호스트의 `8001` 포트에서 접근 가능합니다 (`http://localhost:8001`).

### 예제 스크립트 실행 (Docker 없이)

제공된 예제 스크립트(`exmaple.py`)를 실행하여 Gemini 모델과의 간단한 상호작용을 테스트할 수 있습니다.

```bash
poetry run python exmaple.py
```

또는 Makefile을 사용할 수 있습니다:

```bash
make example
```

### FastAPI 서버 직접 실행 (개발용, Docker 없이)

간단한 FastAPI 서버를 실행할 수 있습니다 (현재는 기본 기능만 제공).

```bash
poetry run uvicorn app.main:app --reload
```

또는 Makefile을 사용할 수 있습니다:

```bash
make run
```

## 프로젝트 구조

```
.
├── .env                # 환경 변수 (직접 생성 및 설정 필요)
├── .gitignore          # Git 추적 제외 파일 목록
├── .python-version     # Python 버전 명시
├── Dockerfile          # Docker 이미지 빌드 설정
├── docker-compose.yml  # Docker Compose 설정 (DB, Web 서비스)
├── Makefile            # 자주 사용하는 명령어 (dev, run, example)
├── README.md           # 프로젝트 설명 (현재 파일)
├── app                 # 애플리케이션 소스 코드
│   ├── __init__.py
│   ├── main.py         # FastAPI 애플리케이션 진입점
│   └── src             # 주요 소스 코드
│       ├── __init__.py
│       ├── clients     # 외부 서비스 클라이언트 (LLM 등)
│       │   ├── __init__.py
│       │   └── chat_client.py # LLM 상호작용 클라이언트
│       ├── llm         # LLM 모델 관련 로직
│       │   ├── __init__.py
│       │   └── llm_models.py  # Grok, Gemini 모델 인터페이스 구현
│       └── models      # 데이터 모델 (Pydantic 등)
│           ├── __init__.py
│           ├── message.py     # 메시지 역할 및 내용 정의
│           └── message_list.py# 메시지 목록 관리
├── exmaple.py          # 클라이언트 사용 예제 스크립트
├── poetry.lock         # 정확한 의존성 버전 고정
└── pyproject.toml      # 프로젝트 메타데이터 및 의존성 정의 (Poetry)
```

## 향후 개선 사항 (TODO)

-   FastAPI 엔드포인트 확장 (채팅 API 등)
-   다양한 LLM 모델 추가 지원
-   오류 처리 및 로깅 개선
-   웹 프론트엔드 구현
-   테스트 코드 작성
