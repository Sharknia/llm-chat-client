from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.models import Keyword, KeywordSite
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.worker_main import get_new_hotdeal_keywords

# --- 테스트 데이터 ---

CRAWLED_DATA_NEW = [
    CrawledKeyword(id="101", title="[새상품] 키보드", link="new_link1", price="10000원"),
    CrawledKeyword(id="102", title="[새상품] 마우스", link="new_link2", price="20000원"),
    CrawledKeyword(id="103", title="[기존상품] 모니터", link="old_link3", price="30000원"),
]

CRAWLED_DATA_NO_NEW = [
    CrawledKeyword(id="103", title="[기존상품] 모니터", link="old_link3", price="30000원"),
    CrawledKeyword(id="104", title="[기존상품] 스피커", link="old_link4", price="40000원"),
]


# --- 테스트 픽스처 ---


@pytest.fixture
async def keyword_in_db(mock_db_session: AsyncSession) -> Keyword:
    """테스트용 키워드를 DB에 생성하고 반환합니다."""
    keyword = Keyword(title="테스트키워드")
    mock_db_session.add(keyword)
    await mock_db_session.commit()
    await mock_db_session.refresh(keyword)
    return keyword


@pytest.fixture
async def keyword_and_site_in_db(
    mock_db_session: AsyncSession, keyword_in_db: Keyword
) -> tuple[Keyword, KeywordSite]:
    """테스트용 키워드와 이전에 크롤링된 사이트 정보를 DB에 생성하고 반환합니다."""
    keyword_site = KeywordSite(
        keyword_id=keyword_in_db.id,
        site_name=SiteName.ALGUMON,
        external_id="103",  # CRAWLED_DATA_NO_NEW의 첫 번째 항목과 일치
        link="old_link3",
        price="30000원",
    )
    mock_db_session.add(keyword_site)
    await mock_db_session.commit()
    await mock_db_session.refresh(keyword_site)
    return keyword_in_db, keyword_site


# --- 테스트 케이스 ---


@pytest.mark.asyncio
async def test_get_new_hotdeal_keywords_first_crawl(
    mock_db_session: AsyncSession, keyword_in_db: Keyword
):
    """
    시나리오 1: 키워드가 처음으로 크롤링될 때
    - 기대: 크롤링된 모든 항목이 '새로운 핫딜'로 반환되고, 첫 번째 항목이 DB에 저장되어야 함
    """
    # GIVEN: 크롤러가 CRAWLED_DATA_NEW를 반환하도록 모킹
    with patch(
        "app.worker_main.AlgumonCrawler.fetchparse", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = CRAWLED_DATA_NEW

        # WHEN: 새로운 핫딜을 조회
        new_deals = await get_new_hotdeal_keywords(mock_db_session, keyword_in_db)

        # THEN: 모든 결과가 반환되어야 함
        assert len(new_deals) == 3
        assert new_deals[0].id == "101"

        # AND: 첫 번째 결과가 DB에 저장되어야 함
        stmt = select(KeywordSite).where(KeywordSite.keyword_id == keyword_in_db.id)
        result = await mock_db_session.execute(stmt)
        saved_site = result.scalars().one()

        assert saved_site is not None
        assert saved_site.external_id == "101"


@pytest.mark.asyncio
async def test_get_new_hotdeal_keywords_no_new_deals(
    mock_db_session: AsyncSession, keyword_and_site_in_db: tuple[Keyword, KeywordSite]
):
    """
    시나리오 2: 새로운 핫딜이 없을 때
    - 기대: 빈 리스트가 반환되어야 함
    """
    # GIVEN: 크롤러가 이전에 저장된 핫딜과 동일한 목록을 반환하도록 모킹
    keyword, _ = keyword_and_site_in_db
    with patch(
        "app.worker_main.AlgumonCrawler.fetchparse", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = CRAWLED_DATA_NO_NEW

        # WHEN: 새로운 핫딜을 조회
        new_deals = await get_new_hotdeal_keywords(mock_db_session, keyword)

        # THEN: 빈 리스트가 반환되어야 함
        assert len(new_deals) == 0


@pytest.mark.asyncio
async def test_get_new_hotdeal_keywords_with_new_deals(
    mock_db_session: AsyncSession, keyword_and_site_in_db: tuple[Keyword, KeywordSite]
):
    """
    시나리오 3: 새로운 핫딜이 발견되었을 때
    - 기대: 이전에 저장된 핫딜을 제외한 새로운 항목만 반환되고, DB는 최신 핫딜로 업데이트되어야 함
    """
    # GIVEN: 크롤러가 새로운 핫딜이 포함된 목록을 반환하도록 모킹
    keyword, old_site_data = keyword_and_site_in_db
    with patch(
        "app.worker_main.AlgumonCrawler.fetchparse", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = CRAWLED_DATA_NEW

        # WHEN: 새로운 핫딜을 조회
        new_deals = await get_new_hotdeal_keywords(mock_db_session, keyword)

        # THEN: 새로운 핫딜 2개만 반환되어야 함 (기존 103 제외)
        assert len(new_deals) == 2
        assert new_deals[0].id == "101"
        assert new_deals[1].id == "102"
        assert not any(deal.id == "103" for deal in new_deals)

        # AND: DB의 external_id가 새로운 핫딜의 ID로 업데이트되어야 함
        await mock_db_session.refresh(old_site_data)
        assert old_site_data.external_id == "101"