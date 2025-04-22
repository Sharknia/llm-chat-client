from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies.auth import create_access_token, create_refresh_token
from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.core.security import hash_password, verify_password
from app.src.domain.user.enums import AuthLevel
from app.src.domain.user.repositories import create_user, get_user_by_email
from app.src.domain.user.schemas import (
    LoginResponse,
    UserLoginRequest,
    UserResponse,
)


async def create_new_user(
    db: AsyncSession,
    email: str,
    nickname: str,
    password: str,
) -> UserResponse:
    """
    새로운 사용자를 생성
    - 이메일 중복 확인
    - 비밀번호 해싱
    - 사용자 생성 (is_active=False, auth_level=USER)
    """
    existing_user = await get_user_by_email(db, email=email)
    if existing_user:
        raise AuthErrors.EMAIL_ALREADY_REGISTERED

    hashed_pwd = hash_password(password)

    new_user = await create_user(
        db=db,
        nickname=nickname,
        email=email,
        hashed_password=hashed_pwd,
        auth_level=AuthLevel.USER,
        is_active=False,
    )

    return UserResponse.model_validate(new_user)


async def login_user(
    db: AsyncSession,
    user_in: UserLoginRequest,
) -> LoginResponse:
    user = await get_user_by_email(db, email=user_in.email)
    if not user:
        raise AuthErrors.USER_NOT_FOUND

    if not verify_password(user_in.password, user.hashed_password):
        raise AuthErrors.INVALID_PASSWORD

    return LoginResponse(
        access_token=create_access_token(
            user.id, user.email, user.nickname, user.auth_level
        ),
        refresh_token=create_refresh_token(db, user.id, user.email),
        user_id=user.id,
    )
