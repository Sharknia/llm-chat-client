import pytest
from fastapi import Response

from app.src.core.dependencies.auth import authenticate_refresh_token
from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.domain.user.models import User
from app.src.domain.user.schemas import LogoutResponse


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "request_data, expected_status, mock_side_effect, expected_response",
    [
        # 정상 요청
        (
            {
                "email": "test@example.com",
                "password": "password123",
                "nickname": "test_user",
            },
            201,
            None,
            None,
        ),
        # 이메일 중복
        (
            {
                "email": "duplicate@example.com",
                "password": "password123",
                "nickname": "duplicate_user",
            },
            AuthErrors.EMAIL_ALREADY_REGISTERED.status_code,
            AuthErrors.EMAIL_ALREADY_REGISTERED,
            {
                "description": AuthErrors.EMAIL_ALREADY_REGISTERED.description,
                "detail": AuthErrors.EMAIL_ALREADY_REGISTERED.detail,
            },
        ),
    ],
)
async def test_post_user(
    mocker,
    add_mock_user,
    mock_client,
    mock_user_data,
    request_data,
    expected_status,
    mock_side_effect,
    expected_response,
):
    """회원가입 API 테스트"""
    # 중복 검사를 위한 기존 유저 추가
    user: User = await add_mock_user(
        email="duplicate@example.com",
        password="password123",
        nickname="duplicate_user",
        is_active=True,
    )
    if mock_side_effect:
        mocker.patch(
            "app.src.domain.user.services.create_new_user",
            side_effect=mock_side_effect,
        )
    else:
        mocker.patch(
            "app.src.domain.user.services.create_new_user",
            return_value=mock_user_data,
        )

    # API 호출
    response: Response = mock_client.post("/api/user/v1/", json=request_data)

    # 응답 검증
    assert response.status_code == expected_status

    if expected_response:
        assert response.json() == expected_response
    else:
        response_data = response.json()
        assert response_data["email"] == mock_user_data["email"]
        assert response_data["nickname"] == mock_user_data["nickname"]
        assert response_data["is_active"] == mock_user_data["is_active"]
        assert response_data["auth_level"] == mock_user_data["auth_level"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "request_data, expected_status, mock_side_effect, expected_response",
    [
        # 정상 요청
        (
            {
                "email": "test@example.com",
                "password": "password123",
            },
            200,
            None,
            None,
        ),
        # 사용자 없음
        (
            {
                "email": "nonexistent@example.com",
                "password": "password123",
            },
            AuthErrors.USER_NOT_FOUND.status_code,
            AuthErrors.USER_NOT_FOUND,
            {
                "description": AuthErrors.USER_NOT_FOUND.description,
                "detail": AuthErrors.USER_NOT_FOUND.detail,
            },
        ),
        # 비밀번호 불일치
        (
            {
                "email": "test@example.com",
                "password": "wrong_password",
            },
            AuthErrors.INVALID_PASSWORD.status_code,
            AuthErrors.INVALID_PASSWORD,
            {
                "description": AuthErrors.INVALID_PASSWORD.description,
                "detail": AuthErrors.INVALID_PASSWORD.detail,
            },
        ),
        # 비활성 사용자
        (
            {
                "email": "inactive@example.com",
                "password": "password123",
            },
            AuthErrors.USER_NOT_ACTIVE.status_code,
            AuthErrors.USER_NOT_ACTIVE,
            {
                "description": AuthErrors.USER_NOT_ACTIVE.description,
                "detail": AuthErrors.USER_NOT_ACTIVE.detail,
            },
        ),
    ],
)
async def test_post_user_login(
    mocker,
    add_mock_user,
    mock_client,
    mock_user_data,
    request_data,
    expected_status,
    mock_side_effect,
    expected_response,
):
    """로그인 API 테스트"""
    # 정상 유저 추가
    user: User = await add_mock_user(
        email="test@example.com",
        password="password123",
        nickname="test_user",
        is_active=True,
    )
    # 비활성 유저 추가
    await add_mock_user(
        email="inactive@example.com",
        password="password123",
        nickname="inactive_user",
        is_active=False,
    )
    if mock_side_effect:
        mocker.patch(
            "app.src.domain.user.services.login_user",
            side_effect=mock_side_effect,
        )
    else:
        mocker.patch(
            "app.src.domain.user.services.login_user", return_value=mock_user_data
        )

    # API 호출
    response: Response = mock_client.post("/api/user/v1/login", json=request_data)

    # 응답 검증
    assert response.status_code == expected_status

    if expected_response:
        assert response.json() == expected_response
    else:
        response_data = response.json()
        # response_data안에 access_token, refresh_token, user_id가 있는지 확인
        assert "access_token" in response_data
        assert "refresh_token" in response_data
        assert "user_id" in response_data


@pytest.mark.asyncio
async def test_post_user_logout(
    mocker,
    mock_authenticated_user,
    override_registered_user,
    mock_client,
):
    """로그아웃 API 테스트"""
    # 로그인 성공으로 오버라이드
    override_registered_user(mock_authenticated_user)

    mocker.patch(
        "app.src.domain.user.v1.router.logout_user",
        return_value=LogoutResponse(),
    )

    # API 호출
    headers = (
        {"Authorization": "Bearer some_refresh_token"}
        if mock_authenticated_user
        else {}
    )
    response: Response = mock_client.post("/api/user/v1/logout", headers=headers)

    # 응답 검증
    assert response.status_code == 200
    assert response.json() == {"message": "Logout successful"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "expected_status, mock_side_effect, expected_response",
    [
        # 정상 요청
        (
            200,
            None,
            {
                "access_token": "access_token_example",
                "refresh_token": "refresh_token_example",
                "user_id": "00000000-0000-0000-0000-000000000000",
            },
        ),
        # 인증 실패
        (
            AuthErrors.INVALID_TOKEN.status_code,
            AuthErrors.INVALID_TOKEN,
            {
                "description": AuthErrors.INVALID_TOKEN.description,
                "detail": AuthErrors.INVALID_TOKEN.detail,
            },
        ),
        # 유효하지 않은 토큰 페이로드
        (
            AuthErrors.INVALID_TOKEN_PAYLOAD.status_code,
            AuthErrors.INVALID_TOKEN_PAYLOAD,
            {
                "description": AuthErrors.INVALID_TOKEN_PAYLOAD.description,
                "detail": AuthErrors.INVALID_TOKEN_PAYLOAD.detail,
            },
        ),
        # 사용자 미존재
        (
            AuthErrors.USER_NOT_FOUND.status_code,
            AuthErrors.USER_NOT_FOUND,
            {
                "description": AuthErrors.USER_NOT_FOUND.description,
                "detail": AuthErrors.USER_NOT_FOUND.detail,
            },
        ),
        # 사용자 비활성화
        (
            AuthErrors.USER_NOT_ACTIVE.status_code,
            AuthErrors.USER_NOT_ACTIVE,
            {
                "description": AuthErrors.USER_NOT_ACTIVE.description,
                "detail": AuthErrors.USER_NOT_ACTIVE.detail,
            },
        ),
        # 리프레시 토큰 만료
        (
            AuthErrors.REFRESH_TOKEN_EXPIRED.status_code,
            AuthErrors.REFRESH_TOKEN_EXPIRED,
            {
                "description": AuthErrors.REFRESH_TOKEN_EXPIRED.description,
                "detail": AuthErrors.REFRESH_TOKEN_EXPIRED.detail,
            },
        ),
    ],
)
async def test_post_user_refresh_token(
    mocker,
    mock_client,
    override_authenticate_refresh_token,
    mock_login_response,
    mock_authenticated_user,
    expected_status,
    mock_side_effect,
    expected_response,
):
    """액세스 토큰 갱신 API 테스트"""
    # authenticate_refresh_token 의존성 함수 동작 오버라이드
    override_authenticate_refresh_token(
        mock_authenticated_user=mock_authenticated_user, error=mock_side_effect
    )

    if mock_side_effect:
        mocker.patch(
            "app.src.domain.user.v1.router.refresh_access_token",
            side_effect=mock_side_effect,
        )
    else:
        mocker.patch(
            "app.src.domain.user.v1.router.refresh_access_token",
            return_value=mock_login_response,
        )

    # API 호출
    headers = (
        {"Authorization": "Bearer some_refresh_token"}
        if mock_authenticated_user
        else {}
    )
    response: Response = mock_client.post("/api/user/v1/token/refresh", headers=headers)

    # 응답 검증
    assert response.status_code == expected_status
    assert response.json() == (expected_response or mock_login_response)

    # authenticate_refresh_token 키가 있는 경우에만 오버라이드 초기화
    if "authenticate_refresh_token" in mock_client.app.dependency_overrides:
        del mock_client.app.dependency_overrides[authenticate_refresh_token]
