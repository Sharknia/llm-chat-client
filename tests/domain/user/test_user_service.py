import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.core.exceptions.base_exceptions import BaseHTTPException
from app.src.domain.user.models import User
from app.src.domain.user.schemas import (
    UserResponse,
)
from app.src.domain.user.services import create_new_user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email, password, nickname, expected_exception",
    [
        # 정상 케이스
        (
            "test@example.com",
            "securepassword",
            "test_user",
            None,
        ),
        # 이메일 중복
        (
            "duplicate@example.com",
            "securepassword",
            "duplicate_user",
            AuthErrors.EMAIL_ALREADY_REGISTERED,
        ),
    ],
)
async def test_register_new_user(
    add_mock_user,
    mock_db_session: AsyncSession,
    email,
    password,
    nickname,
    expected_exception: BaseHTTPException | None,
):
    """회원가입 서비스 테스트"""
    # 중복 검사를 위한 기존 유저 추가
    user: User = await add_mock_user(
        email="duplicate@example.com",
        password="password123",
        nickname="duplicate_user",
        is_active=True,
    )

    if expected_exception:
        try:
            await create_new_user(
                db=mock_db_session,
                email=email,
                password=password,
                nickname=nickname,
            )
        except BaseHTTPException as exc:
            assert exc.status_code == expected_exception.status_code
            assert exc.detail == expected_exception.detail
        else:
            pytest.fail("Expected exception was not raised.")
    else:
        result: UserResponse = await create_new_user(
            db=mock_db_session,
            email=email,
            password=password,
            nickname=nickname,
        )
        assert isinstance(result, UserResponse)
        assert result.email == email
