from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies.db_session import get_db
from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.domain.user.schemas import UserCreateRequest, UserResponse
from app.src.domain.user.services import create_new_user
from app.src.utils.swsagger_helper import create_responses

router = APIRouter(prefix="/v1/user", tags=["user"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="새로운 사용자 생성 (회원가입)",
    responses=create_responses(
        AuthErrors.EMAIL_ALREADY_REGISTERED,
    ),
)
async def signup(
    user_in: UserCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """
    새로운 사용자를 등록합니다.

    - **email**: 사용자 이메일 (로그인 시 사용)
    - **password**: 사용자 비밀번호
    - **nickname**: 사용자 닉네임
    """
    new_user: UserResponse = await create_new_user(db=db, user_in=user_in)
    return new_user
