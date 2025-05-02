from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.exceptions.base_exceptions import BaseHTTPException
from app.src.core.exceptions.client_exceptions import ClientErrors
from app.src.domain.hotdeal.repositories import is_my_keyword
from app.src.domain.hotdeal.schemas import KeywordResponse
from app.src.domain.hotdeal.services import register_keyword, unlink_keyword
from app.src.domain.hotdeal.utils import normalize_keyword


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "title, user_id, expected_exception",
    [
        # 정상 케이스
        (
            "Keyword",
            "00000000-0000-0000-0000-00000000000a",
            None,
        ),
        # 키워드 추가 불가
        (
            "Keyword",
            "00000000-0000-0000-0000-00000000000a",
            ClientErrors.KEYWORD_COUNT_OVERFLOW,
        ),
    ],
)
async def test_register_keyword(
    add_mock_user,
    mock_db_session: AsyncSession,
    title,
    user_id,
    expected_exception: BaseHTTPException | None,
):
    """키워드 등록 서비스 테스트"""
    await add_mock_user(
        id=UUID("00000000-0000-0000-0000-00000000000a"),
        is_active=True,
        nickname="test_user",
        password="validpassword",
    )
    # 키워드 9개를 등록한다.
    for i in range(9):
        await register_keyword(
            db=mock_db_session,
            title=f"Keyword{i}",
            user_id=UUID("00000000-0000-0000-0000-00000000000a"),
        )

    if expected_exception:
        # 하나 더 등록
        await register_keyword(
            db=mock_db_session,
            title="Keyword10",
            user_id=UUID("00000000-0000-0000-0000-00000000000a"),
        )
        try:
            await register_keyword(
                db=mock_db_session,
                title=title,
                user_id=UUID(user_id),
            )
        except BaseHTTPException as exc:
            assert exc.status_code == expected_exception.status_code
            assert exc.detail == expected_exception.detail
        else:
            pytest.fail("Expected exception was not raised.")
    else:
        result: KeywordResponse = await register_keyword(
            db=mock_db_session,
            title=title,
            user_id=UUID(user_id),
        )
        assert isinstance(result, KeywordResponse)
        assert result.title == normalize_keyword(title)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "keyword_id, user_id, expected_exception",
    [
        # 정상 케이스
        (
            1,
            "00000000-0000-0000-0000-00000000000a",
            None,
        ),
        # 키워드 존재하지 않음
        (
            1,
            "00000000-0000-0000-0000-00000000000a",
            ClientErrors.KEYWORD_NOT_FOUND,
        ),
    ],
)
async def test_unlink_keyword(
    add_mock_user,
    mock_db_session: AsyncSession,
    keyword_id,
    user_id,
    expected_exception: BaseHTTPException | None,
):
    """키워드 삭제 서비스 테스트"""
    await add_mock_user(
        id=UUID(user_id),
        is_active=True,
        nickname="test_user",
        password="validpassword",
    )

    if expected_exception:
        try:
            await unlink_keyword(
                db=mock_db_session,
                keyword_id=keyword_id,
                user_id=UUID(user_id),
            )
        except BaseHTTPException as exc:
            assert exc.status_code == expected_exception.status_code
            assert exc.detail == expected_exception.detail
        else:
            pytest.fail("Expected exception was not raised.")
    else:
        # 키워드 등록한다.
        new_keyword: KeywordResponse = await register_keyword(
            db=mock_db_session,
            title="Keyword",
            user_id=UUID(user_id),
        )
        # 키워드 삭제
        await unlink_keyword(
            db=mock_db_session,
            keyword_id=new_keyword.id,
            user_id=UUID(user_id),
        )
        # 키워드 삭제 후 키워드 존재 여부 확인
        result = await is_my_keyword(mock_db_session, UUID(user_id), new_keyword.id)
        assert not result
