from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies.auth import registered_user
from app.src.core.dependencies.db_session import get_db
from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.core.exceptions.client_exceptions import ClientErrors
from app.src.domain.hotdeal.schemas import KeywordCreateRequest, KeywordResponse
from app.src.domain.hotdeal.services import register_keyword, unlink_keyword
from app.src.domain.user.schemas import (
    AuthenticatedUser,
)
from app.src.utils.swsagger_helper import create_responses

router = APIRouter(prefix="/v1", tags=["hotdeal"])


# 키워드 등록하기
@router.post(
    "/keywords",
    status_code=status.HTTP_201_CREATED,
    summary="키워드 등록하기",
    responses=create_responses(
        AuthErrors.INVALID_TOKEN,
        AuthErrors.INVALID_TOKEN_PAYLOAD,
        AuthErrors.USER_NOT_ACTIVE,
        AuthErrors.USER_NOT_FOUND,
        ClientErrors.KEYWORD_COUNT_OVERFLOW,
    ),
)
async def post_keyword(
    request: KeywordCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    login_user: Annotated[AuthenticatedUser, Depends(registered_user)],
) -> KeywordResponse:
    result: KeywordResponse = await register_keyword(
        db=db,
        title=request.title,
        user_id=login_user.user_id,
    )
    return result


# 내 키워드 삭제하기
@router.delete(
    "/keywords/{keyword_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="내 키워드 삭제하기",
    responses=create_responses(
        AuthErrors.INVALID_TOKEN,
        AuthErrors.INVALID_TOKEN_PAYLOAD,
        AuthErrors.USER_NOT_ACTIVE,
        AuthErrors.USER_NOT_FOUND,
        ClientErrors.KEYWORD_NOT_FOUND,
    ),
)
async def delete_my_keyword(
    keyword_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    login_user: Annotated[AuthenticatedUser, Depends(registered_user)],
) -> None:
    await unlink_keyword(db=db, keyword_id=keyword_id, user_id=login_user.user_id)
    return


# 내 키워드 리스토 보기
