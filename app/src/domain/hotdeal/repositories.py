from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.src.domain.hotdeal.models import Keyword
from app.src.domain.user.models import User


# 새로운 키워드 등록
async def create_keyword(
    db: AsyncSession,
    title: str,
) -> Keyword:
    new_keyword = Keyword(title=title)
    db.add(new_keyword)
    await db.commit()
    await db.refresh(new_keyword)
    return new_keyword


# title을 받아서 키워드 조회
async def get_keyword_by_title(
    db: AsyncSession,
    title: str,
) -> Keyword | None:
    result = await db.execute(select(Keyword).filter(Keyword.title == title))
    return result.scalar_one_or_none()


# 내 키워드 갯수 확인
async def get_my_keyword_count(
    db: AsyncSession,
    user_id: UUID,
) -> int:
    result = await db.execute(
        select(func.count(Keyword.id)).filter(Keyword.users.any(User.id == user_id))
    )
    return result.scalar_one_or_none()


# 내 키워드 추가
async def add_my_keyword(
    db: AsyncSession,
    user_id: UUID,
    keyword_id: int,
) -> None:
    result = await db.execute(
        select(User).options(selectinload(User.keywords)).filter(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    keyword = await db.get(Keyword, keyword_id)

    if user and keyword:
        user.keywords.append(keyword)
        await db.commit()
