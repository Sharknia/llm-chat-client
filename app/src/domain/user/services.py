from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.core.security import hash_password
from app.src.domain.user.enums import AuthLevel
from app.src.domain.user.repositories import create_user, get_user_by_email
from app.src.domain.user.schemas import UserCreateRequest, UserResponse


async def create_new_user(
    db: AsyncSession,
    user_in: UserCreateRequest,
) -> UserResponse:
    """
    새로운 사용자를 생성
    - 이메일 중복 확인
    - 비밀번호 해싱
    - 사용자 생성 (is_active=False, auth_level=USER)
    """
    existing_user = await get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise AuthErrors.EMAIL_ALREADY_REGISTERED

    hashed_pwd = hash_password(user_in.password)

    new_user = await create_user(
        db=db,
        nickname=user_in.nickname,
        email=user_in.email,
        hashed_password=hashed_pwd,
        auth_level=AuthLevel.USER,
        is_active=False,
    )

    return UserResponse.model_validate(new_user)
