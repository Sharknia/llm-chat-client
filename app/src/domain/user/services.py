from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies.auth import create_access_token, create_refresh_token
from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.core.security import hash_password, verify_password
from app.src.domain.user.enums import AuthLevel
from app.src.domain.user.repositories import (
    create_user,
    delete_refresh_token,
    get_user_by_email,
    get_user_by_id,
)
from app.src.domain.user.schemas import (
    LoginResponse,
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
    email: str,
    password: str,
) -> LoginResponse:
    user = await get_user_by_email(db, email=email)
    if not user:
        raise AuthErrors.USER_NOT_FOUND

    if not verify_password(password, user.hashed_password):
        raise AuthErrors.INVALID_PASSWORD

    if not user.is_active:
        raise AuthErrors.USER_NOT_ACTIVE

    return LoginResponse(
        access_token=await create_access_token(
            user.id, user.email, user.nickname, user.auth_level
        ),
        refresh_token=await create_refresh_token(db, user.id, user.email),
        user_id=str(user.id),
    )


async def logout_user(db: AsyncSession, user_id: UUID) -> None:
    # 실제 있는 유저인지 확인
    user = await get_user_by_id(db, user_id)
    if not user:
        raise AuthErrors.USER_NOT_FOUND

    # 활성화 상태 확인
    if not user.is_active:
        raise AuthErrors.USER_NOT_ACTIVE

    # 액세스 토큰을 블랙리스트에 등록하는 로직은 생략
    await delete_refresh_token(db, user_id)
    return None


async def refresh_access_token(
    db: AsyncSession,
    user_id: UUID,
    email: str,
) -> LoginResponse:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise AuthErrors.USER_NOT_FOUND

    if not user.is_active:
        raise AuthErrors.USER_NOT_ACTIVE

    access_token = await create_access_token(
        user_id=user_id,
        email=email,
        nickname=user.nickname,
        auth_level=user.auth_level,
    )
    refresh_token = await create_refresh_token(
        db=db,
        user_id=user_id,
        email=email,
    )
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=str(user_id),
    )
