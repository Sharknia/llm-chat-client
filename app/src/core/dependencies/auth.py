from datetime import UTC, datetime, timedelta

from fastapi import Depends, Header
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy.orm import Session

from app.src.core.config import settings
from app.src.core.dependencies.db_session import get_db
from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.domain.user.repositories import (
    check_user_active,
    delete_refresh_token,
    save_refresh_token,
    verify_refresh_token,
)
from app.src.domain.user.schemas import AuthenticatedUser

ALGORITHM = "HS256"


async def create_access_token(
    user_id: int,
    email: str,
    expires_delta: timedelta = timedelta(minutes=15),
) -> str:
    """
    Access Token 생성 함수
    """
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(UTC) + expires_delta,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


async def create_refresh_token(
    db: Session,
    user_id: int,
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
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")

        if user_id is None or email is None:
            raise AuthErrors.INVALID_TOKEN_PAYLOAD
        # 인증된 사용자 정보 반환
        return AuthenticatedUser(user_id=user_id, email=email)

    except JWTError:
        raise AuthErrors.INVALID_TOKEN


# 헤더에 담겨온 리프레쉬 토큰 검증
async def authenticate_refresh_token(
    db: Session = Depends(get_db),
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
        except ValueError:
            raise AuthErrors.INVALID_TOKEN

        # 사용된 리프레시 토큰 삭제
        await delete_refresh_token(db, user_id)

        # 인증된 사용자 정보 반환
        return AuthenticatedUser(user_id=user_id, email=email)

    except ExpiredSignatureError:
        raise AuthErrors.REFRESH_TOKEN_EXPIRED
    except JWTError:
        raise AuthErrors.INVALID_TOKEN


async def authenticate_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    """
    사용자 인증 의존성 함수 : 이메일 인증 확인
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthErrors.NOT_AUTHENTICATED

    # 토큰 추출
    token = authorization.split(" ")[1]

    try:
        # 토큰 검증 및 디코딩
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")

        if user_id is None or email is None:
            raise AuthErrors.INVALID_TOKEN

        # 사용자 조회 및 이메일 인증 여부 확인
        is_active_user = await check_user_active(db, user_id)
        if not is_active_user:
            raise AuthErrors.USER_NOT_ACTIVE

        # 인증된 사용자 정보 반환
        return AuthenticatedUser(user_id=user_id, email=email)
    except ExpiredSignatureError:
        raise AuthErrors.ACCESS_TOKEN_EXPIRED
    except JWTError:
        raise AuthErrors.INVALID_TOKEN


async def create_email_verification_token(
    user_id: int,
) -> str:
    """
    이메일 인증을 위한 JWT 생성
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.now(UTC) + timedelta(hours=24),
        "purpose": "email_verification",
    }
    return jwt.encode(payload, settings.EMAIL_SECRET_KEY, algorithm=ALGORITHM)


async def create_password_reset_token(
    user_id: int,
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
    except ExpiredSignatureError:
        raise AuthErrors.ACCESS_TOKEN_EXPIRED
    except JWTError:
        raise AuthErrors.INVALID_TOKEN
