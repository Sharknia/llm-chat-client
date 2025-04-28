from uuid import UUID

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.exceptions.client_exceptions import ClientErrors
from app.src.domain.hotdeal.models import Keyword
from app.src.domain.hotdeal.repositories import (
    add_my_keyword,
    create_keyword,
    get_keyword_by_title,
    get_my_keyword_count,
)
from app.src.domain.hotdeal.schemas import KeywordResponse
from app.src.domain.hotdeal.utils import normalize_keyword

router = APIRouter(prefix="/v1", tags=["hotdeal"])


async def register_keyword(
    db: AsyncSession,
    title: str,
    user_id: UUID,
) -> KeywordResponse:
    # 키워드에서 공백 제거하고 소문자로 변환
    title = normalize_keyword(title)
    # 이미 존재하는 키워드인지 확인
    keyword: Keyword | None = await get_keyword_by_title(db, title)
    # 존재하지 않을 경우 키워드 등록
    if keyword is None:
        keyword = await create_keyword(db, title)
    # 내 키워드 갯수 확인, 지금 이미 10개라면 추가 불가
    my_keyword_count: int = await get_my_keyword_count(db, user_id)
    if my_keyword_count >= 10:
        raise ClientErrors.KEYWORD_COUNT_OVERFLOW
    # 내 키워드로 등록
    try:
        await add_my_keyword(db, user_id, keyword.id)
    except:
        raise ClientErrors.DUPLICATE_KEYWORD_REGISTRATION
    return KeywordResponse(
        title=keyword.title,
    )
