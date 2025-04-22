import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, Header
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.config import settings
from app.src.core.dependencies.db_session import get_db
from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.domain.user.enums import AuthLevel
from app.src.domain.user.repositories import (
    check_user_active,
    delete_refresh_token,
    save_refresh_token,
    verify_refresh_token,
)
from app.src.domain.user.schemas import AuthenticatedUser

ALGORITHM = "HS256"

# Annotated를 사용하여 DB 세션 의존성 타입 정의
DBSession = Annotated[AsyncSession, Depends(get_db)]


async def create_access_token(
    user_id: uuid.UUID,
    email: str,
    nickname: str,
    auth_level: AuthLevel,
    expires_delta: timedelta = timedelta(minutes=15),
) -> str:
    """
    Access Token 생성 함수
    """
    payload = {
        "user_id": str(user_id),
        "email": email,
        "nickname": nickname,
        "auth_level": auth_level.value,
        "exp": datetime.now(UTC) + expires_delta,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


async def create_refresh_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    email: str,
    expires_delta: timedelta = timedelta(days=7),
) -> str:
    """
    Refresh Token 생성 함수
    """
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(UTC) + expires_delta,  # 만료 시간 추가
    }
    refresh_token = jwt.encode(
        payload, settings.REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM
    )
    # db에 리프레시 토큰 저장
    await save_refresh_token(db, user_id, refresh_token)
    return refresh_token


async def registered_user(
    authorization: str = Header(None),
) -> AuthenticatedUser:
    """
    사용자 가입 의존성 함수 : 단순 가입만 확인
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthErrors.INVALID_TOKEN

    # 토큰 추출
    token = authorization.split(" ")[1]

    try:
        # 토큰 검증 및 디코딩
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("user_id")
        email: str = payload.get("email")
        nickname: str = payload.get("nickname")
        auth_level_value: int = payload.get("auth_level")

        if (
            user_id_str is None
            or email is None
            or nickname is None
            or auth_level_value is None
        ):
            raise AuthErrors.INVALID_TOKEN_PAYLOAD

        # user_id 형식 검증 추가
        try:
            # UUID 변환 시도 (실제 사용은 안하지만 형식 검증용)
            _ = uuid.UUID(user_id_str)
        except ValueError as e:
            # UUID 변환 실패 시 잘못된 페이로드
            raise AuthErrors.INVALID_TOKEN_PAYLOAD from e

        try:
            auth_level = AuthLevel(auth_level_value)
        except ValueError as e:
            raise AuthErrors.INVALID_TOKEN_PAYLOAD from e

        # AuthenticatedUser 생성 시에는 문자열 user_id 전달
        return AuthenticatedUser(
            user_id=user_id_str, email=email, nickname=nickname, auth_level=auth_level
        )

    except JWTError as e:
        raise AuthErrors.INVALID_TOKEN from e


# 헤더에 담겨온 리프레쉬 토큰 검증
async def authenticate_refresh_token(
    db: DBSession,
    authorization: str = Header(None),
) -> AuthenticatedUser:
    """
    리프레시 토큰 검증 함수
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthErrors.INVALID_TOKEN

    # 토큰 추출
    token = authorization.split(" ")[1]

    try:
        # 토큰 검증 및 디코딩
        payload = jwt.decode(
            token, settings.REFRESH_TOKEN_SECRET_KEY, algorithms=[ALGORITHM]
        )
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")

        if user_id is None or email is None:
            raise AuthErrors.INVALID_TOKEN_PAYLOAD

        # db에 저장된 리프레시 토큰과 비교
        try:
            if not await verify_refresh_token(db, user_id, token):
                raise AuthErrors.INVALID_TOKEN
        # 유저가 발견되지 않은 경우
        except ValueError as e:
            raise AuthErrors.INVALID_TOKEN from e

        # 사용된 리프레시 토큰 삭제
        await delete_refresh_token(db, user_id)

        # 인증된 사용자 정보 반환
        return AuthenticatedUser(
            user_id=user_id, email=email, auth_level=AuthLevel.USER
        )

    except ExpiredSignatureError as e:
        raise AuthErrors.REFRESH_TOKEN_EXPIRED from e
    except JWTError as e:
        raise AuthErrors.INVALID_TOKEN from e


async def authenticate_user(
    db: DBSession,
    authorization: str = Header(None),
) -> AuthenticatedUser:
    """
    사용자 인증 의존성 함수 : 활성 상태인 일반 사용자(USER 레벨 이상) 확인
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthErrors.NOT_AUTHENTICATED

    # 토큰 추출
    token = authorization.split(" ")[1]

    try:
        # 토큰 검증 및 디코딩
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("user_id")
        email: str = payload.get("email")
        nickname: str = payload.get("nickname")
        auth_level_value: int = payload.get("auth_level")

        if (
            user_id_str is None
            or email is None
            or nickname is None
            or auth_level_value is None
        ):
            raise AuthErrors.INVALID_TOKEN_PAYLOAD

        try:
            auth_level = AuthLevel(auth_level_value)
        except ValueError as e:
            raise AuthErrors.INVALID_TOKEN_PAYLOAD from e

        # 사용자 활성 상태 확인 (UUID로 변환하여 전달)
        try:
            user_uuid = uuid.UUID(user_id_str)  # 문자열을 UUID로 변환
        except ValueError as e:
            # UUID 변환 실패 시 잘못된 토큰으로 간주
            raise AuthErrors.INVALID_TOKEN_PAYLOAD from e

        is_active_user = await check_user_active(db, user_uuid)  # UUID 객체 전달
        if not is_active_user:
            raise AuthErrors.USER_NOT_ACTIVE

        # --- 권한 레벨 확인 추가 (USER 이상) ---
        if auth_level.value < AuthLevel.USER.value:
            raise AuthErrors.INSUFFICIENT_PERMISSIONS

        # AuthenticatedUser 생성 시에는 문자열 user_id 전달 (Pydantic이 UUID로 변환)
        return AuthenticatedUser(
            user_id=user_id_str, email=email, nickname=nickname, auth_level=auth_level
        )
    except ExpiredSignatureError as e:
        raise AuthErrors.ACCESS_TOKEN_EXPIRED from e
    except JWTError as e:
        raise AuthErrors.INVALID_TOKEN from e


# ---- 관리자 인증 함수 추가 ----
async def authenticate_admin_user(
    db: DBSession,
    authorization: str = Header(None),
) -> AuthenticatedUser:
    """
    관리자 인증 의존성 함수 : 활성 상태인 관리자(ADMIN 레벨 이상) 확인
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthErrors.NOT_AUTHENTICATED

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("user_id")
        email: str = payload.get("email")
        nickname: str = payload.get("nickname")
        auth_level_value: int = payload.get("auth_level")

        if (
            user_id_str is None
            or email is None
            or nickname is None
            or auth_level_value is None
        ):
            raise AuthErrors.INVALID_TOKEN_PAYLOAD

        try:
            auth_level = AuthLevel(auth_level_value)
        except ValueError as e:
            raise AuthErrors.INVALID_TOKEN_PAYLOAD from e

        # 사용자 활성 상태 확인 (UUID로 변환하여 전달)
        try:
            user_uuid = uuid.UUID(user_id_str)  # 문자열을 UUID로 변환
        except ValueError as e:
            raise AuthErrors.INVALID_TOKEN_PAYLOAD from e

        is_active_user = await check_user_active(db, user_uuid)  # UUID 객체 전달
        if not is_active_user:
            raise AuthErrors.USER_NOT_ACTIVE

        # --- 권한 레벨 확인 추가 (ADMIN 이상) ---
        if auth_level.value < AuthLevel.ADMIN.value:
            raise AuthErrors.INSUFFICIENT_PERMISSIONS

        # AuthenticatedUser 생성 시에는 문자열 user_id 전달
        return AuthenticatedUser(
            user_id=user_id_str, email=email, nickname=nickname, auth_level=auth_level
        )
    except ExpiredSignatureError as e:
        raise AuthErrors.ACCESS_TOKEN_EXPIRED from e
    except JWTError as e:
        raise AuthErrors.INVALID_TOKEN from e


async def create_password_reset_token(
    user_id: uuid.UUID,
) -> str:
    """
    비밀번호 재설정을 위한 JWT 생성
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        "purpose": "password_reset",
    }
    return jwt.encode(payload, settings.PASSWORD_SECRET_KEY, algorithm=ALGORITHM)


async def verify_password_reset_token(
    token: str,
) -> int:
    """
    비밀번호 재설정 JWT 검증
    """
    try:
        payload = jwt.decode(
            token, settings.PASSWORD_SECRET_KEY, algorithms=[ALGORITHM]
        )
        user_id: int = payload.get("user_id")
        purpose: str = payload.get("purpose")

        if user_id is None or purpose != "password_reset":
            raise AuthErrors.INVALID_TOKEN

        return user_id
    except ExpiredSignatureError as e:
        raise AuthErrors.ACCESS_TOKEN_EXPIRED from e
    except JWTError as e:
        raise AuthErrors.INVALID_TOKEN from e
