import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.src.core.config import settings
from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.models import Keyword, KeywordSite
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.src.domain.mail.models import MailLog
from app.src.domain.user.models import User, user_keywords

# 프로젝트의 공통 설정과 DB 세션을 가져옵니다
from app.src.Infrastructure.crawling.base_crawler import BaseCrawler
from app.src.Infrastructure.crawling.crawlers.algumon import AlgumonCrawler
from app.src.Infrastructure.crawling.proxy_manager import ProxyManager

_unused = (User, user_keywords, MailLog)

ASYNC_DATABASE_URL = (
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    .replace("db", "localhost", 1)
    .replace("5432", "5433")
)

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


PROXY_MANAGER = ProxyManager()

# keyword_id - CrawledKeyword의 딕셔너리
id_to_crawled_keyword: dict[int, CrawledKeyword] = {}


async def handle_keyword(
    keyword: Keyword,
    session: AsyncSession,
) -> list[CrawledKeyword]:
    """
    단일 키워드를 크롤링하고 크롤링 결과를 갱신
    """
    print(f"[INFO] 키워드 처리: {keyword.title}")

    crwaled_data: list[CrawledKeyword] = await get_new_hotdeal_keywords(
        session=session,
        keyword=keyword,
    )

    if crwaled_data:
        id_to_crawled_keyword[keyword.id] = crwaled_data
    else:
        print(f"[INFO] 키워드 처리: {keyword.title} 크롤링 결과 없음")


async def get_new_hotdeal_keywords(
    session: AsyncSession,
    keyword: Keyword,
) -> list[CrawledKeyword]:
    """
    새로운 핫딜 키워드를 조회합니다.
    """
    # 해당 키워드에 대해 크롤링
    algumon_crawler: BaseCrawler = AlgumonCrawler(keyword=keyword.title)

    products: list[CrawledKeyword] = algumon_crawler.fetchparse()

    # 기존 크롤링 결과 조회
    stmt = select(KeywordSite).where(
        KeywordSite.site_name == SiteName.ALGUMON,
        KeywordSite.keyword_id == keyword.id,
    )
    result: Result[KeywordSite] = await session.execute(stmt)
    # 유니크 키이므로 단 하나만 조회됨
    result: KeywordSite | None = result.scalars().one_or_none()

    is_first_product: bool = True
    first_product: KeywordSite | None = None

    return_result: list[CrawledKeyword] = []

    for product in products:
        # 첫번째 프로덕트인데, 기존 크롤링 결과가 없는 경우
        if is_first_product and not result:
            first_product = KeywordSite(
                keyword_id=keyword.id,
                site_name=SiteName.ALGUMON,
                external_id=product.id,
                link=product.link,
                price=product.price,
                meta_data=product.meta_data,
            )
            session.add(first_product)
            await session.commit()
            return [product]
        # 첫번째 프로덕트인데, 기존 크롤링 결과가 있는데 이번것과 아이디가 같은 경우는 그냥 빈 리스트 리턴 (새 핫딜 없음)
        elif is_first_product and result and result.external_id == product.id:
            return []
        # 첫번째 프로덕트인데, 기존 크롤링 결과가 있고 아이디가 다른 경우는 첫번째 프로덕트 박제 (추후 업데이트)
        elif is_first_product and result and result.external_id != product.id:
            first_product = product

        # 첫번째 프로덕트가 아니라면, 지금 프로덕트의 아이디와 기존 저장된 프로덕트 아이디가 같다면 return
        elif not is_first_product and result and result.external_id == product.id:
            # first_product update
            result.external_id = product.id
            result.link = product.link
            result.price = product.price
            result.meta_data = product.meta_data
            result.wdate = datetime.now()
            await session.commit()
            return return_result

        return_result.append(product)
        is_first_product = False
    return result


async def job():
    """
    사용자와 연결된 키워드만 불러와 병렬로 처리합니다.
    """
    PROXY_MANAGER.fetch_proxies()
    async with AsyncSessionLocal() as session:
        # 사용자와 매핑된 키워드만 조회
        stmt = select(Keyword).where(Keyword.users.any())
        result = await session.execute(stmt)
        keywords = result.scalars().all()

    tasks = [handle_keyword(kw, session) for kw in keywords]
    PROXY_MANAGER.reset_proxies()
    await asyncio.gather(*tasks)


def main():
    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

    # 매 시 0분, 30분에 job() 실행
    scheduler.add_job(
        lambda: asyncio.create_task(job()),
        trigger=CronTrigger(minute="0,30"),
        id="hotdeal_worker",
        replace_existing=True,
    )

    scheduler.start()
    print("[INFO] Worker 스케줄러 시작: 매 시 정각 및 30분마다 크롤링 및 메일 발송")

    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        print("[INFO] Worker 종료 중...")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(job())
    # main()
