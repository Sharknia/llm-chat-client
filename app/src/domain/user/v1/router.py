from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies.auth import authenticate_refresh_token, registered_user
from app.src.core.dependencies.db_session import get_db
from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.domain.user.schemas import (
    AuthenticatedUser,
    LoginResponse,
    LogoutResponse,
    UserCreateRequest,
    UserLoginRequest,
    UserResponse,
)
from app.src.domain.user.services import (
    create_new_user,
    login_user,
    logout_user,
    refresh_access_token,
)
from app.src.utils.swsagger_helper import create_responses

router = APIRouter(prefix="/v1", tags=["user"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="새로운 사용자 생성 (회원가입)",
    responses=create_responses(
        AuthErrors.EMAIL_ALREADY_REGISTERED,
    ),
)
async def signup(
    request: UserCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """
    새로운 사용자를 등록합니다.

    - **email**: 사용자 이메일 (로그인 시 사용)
    - **password**: 사용자 비밀번호
    - **nickname**: 사용자 닉네임
    """
    new_user: UserResponse = await create_new_user(
        db=db,
        email=request.email,
        nickname=request.nickname,
        password=request.password,
    )
    return new_user


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="사용자 로그인",
    responses=create_responses(
        AuthErrors.USER_NOT_FOUND,
        AuthErrors.INVALID_PASSWORD,
        AuthErrors.USER_NOT_ACTIVE,
    ),
)
async def login(
    request: UserLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LoginResponse:
    """
    사용자 로그인

    - **email**: 사용자 이메일 (로그인 시 사용)
    - **password**: 사용자 비밀번호
    """
    user: LoginResponse = await login_user(
        db=db,
        email=request.email,
        password=request.password,
    )
    return user


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="사용자 로그아웃",
    responses=create_responses(
        AuthErrors.INVALID_TOKEN,
        AuthErrors.INVALID_TOKEN_PAYLOAD,
        AuthErrors.USER_NOT_ACTIVE,
        AuthErrors.USER_NOT_FOUND,
    ),
)
async def logout(
    db: Annotated[AsyncSession, Depends(get_db)],
    login_user: Annotated[AuthenticatedUser, Depends(registered_user)],
) -> LogoutResponse:
    """
    사용자 로그아웃
    """
    await logout_user(db, login_user.user_id)
    return LogoutResponse()


# 액세스 토큰 갱신
@router.post(
    "/token/refresh",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="액세스 토큰 갱신",
    responses=create_responses(
        AuthErrors.INVALID_TOKEN,
        AuthErrors.INVALID_TOKEN_PAYLOAD,
        AuthErrors.USER_NOT_ACTIVE,
        AuthErrors.USER_NOT_FOUND,
        AuthErrors.REFRESH_TOKEN_EXPIRED,
    ),
)
async def refresh_token(
    db: Annotated[AsyncSession, Depends(get_db)],
    login_user: Annotated[AuthenticatedUser, Depends(authenticate_refresh_token)],
) -> LoginResponse:
    """
    액세스 토큰 갱신
    """
    result = await refresh_access_token(
        db=db,
        user_id=login_user.user_id,
        email=login_user.email,
    )
    return result


# 내 정보 가져오기
@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="내 정보 가져오기",
)
async def get_me(
    login_user: Annotated[AuthenticatedUser, Depends(registered_user)],
) -> UserResponse:
    """
    내 정보 가져오기
    """
    return login_user
