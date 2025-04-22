import pytest
from fastapi import Response

from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.domain.user.models import User


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
        print(response.json())
        print(expected_response)
        assert response.json() == expected_response
    else:
        response_data = response.json()
        assert response_data["email"] == mock_user_data["email"]
        assert response_data["nickname"] == mock_user_data["nickname"]
        assert response_data["is_active"] == mock_user_data["is_active"]
        assert response_data["auth_level"] == mock_user_data["auth_level"]
