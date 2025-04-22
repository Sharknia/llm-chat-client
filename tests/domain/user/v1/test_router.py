# tests/domain/user/v1/test_router.py
import uuid
from unittest.mock import AsyncMock

import pytest

# TestClient 임포트
from fastapi.testclient import TestClient

# httpx 관련 임포트 제거 또는 주석 처리
# from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.src.core.dependencies.db_session import get_db
from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.domain.user.enums import AuthLevel

# pytestmark = pytest.mark.asyncio # 동기 테스트이므로 제거 또는 주석 처리


# --- 의존성 오버라이드를 위한 설정 ---
# override_get_db는 async로 유지 (FastAPI가 내부적으로 처리 가능할 수 있음)
async def override_get_db():
    mock_session = AsyncMock(spec=AsyncSession)
    yield mock_session


# --- 테스트 클라이언트 픽스처 (TestClient 사용) ---
@pytest.fixture(scope="function")
def test_client() -> TestClient:  # 반환 타입을 TestClient로 변경
    app.dependency_overrides[get_db] = override_get_db
    # TestClient 직접 사용, transport/base_url 불필요
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# /api/v1/user/signup 테스트 (동기 함수로 변경)
@pytest.mark.parametrize(
    "request_data, expected_status, mock_service_return, mock_service_exception, expected_response_detail",
    [
        # 1. 정상 회원가입 요청 (성공)
        (
            {
                "email": "test@example.com",
                "password": "password123",
                "nickname": "testuser",
            },
            201,  # status.HTTP_201_CREATED
            # User 모델 객체와 유사한 딕셔너리 반환 가정
            {
                "id": uuid.uuid4(),  # 테스트 내에서는 실제 ID와 비교하지 않음
                "email": "test@example.com",
                "nickname": "testuser",
                "is_active": False,
                "auth_level": AuthLevel.USER,
            },
            None,  # 예외 없음
            None,  # 성공 시엔 detail 없음
        ),
        # 2. 이메일 중복 요청 (실패)
        (
            {
                "email": "duplicate@example.com",
                "password": "password123",
                "nickname": "duplicate_user",
            },
            400,  # status.HTTP_400_BAD_REQUEST (라우터에서 변환)
            None,  # 성공 응답 없음
            AuthErrors.EMAIL_ALREADY_REGISTERED,  # 서비스에서 발생시킬 예외
            AuthErrors.EMAIL_ALREADY_REGISTERED.detail,  # 라우터에서 반환하는 detail 메시지
        ),
        # 3. 요청 데이터 부족 (예: nickname 누락) - FastAPI/Pydantic 레벨에서 처리됨 (422)
        (
            {
                "email": "incomplete@example.com",
                "password": "password123",
            },  # nickname 누락
            422,  # Unprocessable Entity
            None,
            None,
            None,  # Pydantic 에러 메시지는 복잡하므로 여기서는 상태 코드만 확인
        ),
        # 4. 잘못된 이메일 형식 - FastAPI/Pydantic 레벨에서 처리됨 (422)
        (
            {
                "email": "invalid-email",
                "password": "password123",
                "nickname": "invalid",
            },
            422,
            None,
            None,
            None,
        ),
    ],
)
def test_signup(  # async 제거
    mocker,
    test_client: TestClient,  # 타입을 TestClient로 변경
    request_data,
    expected_status,
    mock_service_return,
    mock_service_exception,
    expected_response_detail,
):
    """
    POST /api/v1/user/signup 회원가입 API 테스트
    - 성공 케이스 (201)
    - 실패 케이스 (이메일 중복 - 400)
    - 실패 케이스 (입력값 유효성 검사 - 422)
    """

    # 서비스 계층(create_new_user) 모킹 (패치 대상 변경)
    mock_create_user = mocker.patch(
        "app.src.domain.user.v1.router.create_new_user",  # 라우터 모듈의 함수를 직접 패치
        autospec=True,
        side_effect=mock_service_exception,
        return_value=mock_service_return,
    )

    # API 호출 (동기 방식)
    response = test_client.post("/api/v1/user/signup", json=request_data)  # await 제거

    # 응답 검증
    assert response.status_code == expected_status

    # 성공 케이스 검증 (201)
    if expected_status == 201:
        # 동기 함수 호출 검증으로 변경
        mock_create_user.assert_called_once()
        response_data = response.json()
        # id는 동적으로 생성되므로 타입을 확인하고, 나머지 필드를 비교
        assert isinstance(uuid.UUID(response_data["id"]), uuid.UUID)
        # mock_service_return의 값과 비교
        assert response_data["email"] == mock_service_return["email"]
        assert response_data["nickname"] == mock_service_return["nickname"]
        assert response_data["is_active"] == mock_service_return["is_active"]
        assert response_data["auth_level"] == mock_service_return["auth_level"].value

    # 이메일 중복 케이스 검증 (400)
    elif expected_status == 400:
        # 동기 함수 호출 검증
        mock_create_user.assert_called_once()
        response_data = response.json()
        assert response_data["detail"] == expected_response_detail

    # 입력값 유효성 검사 실패 케이스 (422)
    elif expected_status == 422:
        # 동기 함수 호출 검증
        mock_create_user.assert_not_called()
        # 상세 에러 메시지 검증은 생략 (Pydantic 에러 구조 복잡)
