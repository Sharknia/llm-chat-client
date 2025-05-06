import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from app.src.core.config import settings
from app.src.core.logger import logger
from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.models import Keyword, KeywordSite
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.src.domain.mail.models import MailLog
from app.src.domain.user.models import User, user_keywords

# 프로젝트의 공통 설정과 DB 세션을 가져옵니다
from app.src.Infrastructure.crawling.base_crawler import BaseCrawler
from app.src.Infrastructure.crawling.crawlers.algumon import AlgumonCrawler
from app.src.Infrastructure.crawling.proxy_manager import ProxyManager
from app.src.Infrastructure.mail.mail_manager import (
    make_hotdeal_email_content,
    send_email,
)

# User 모델을 사용하므로 _unused 튜플에서 제거하거나 주석 처리합니다.
_unused = (user_keywords, MailLog)

ASYNC_DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://", 1
)
if settings.ENVIRONMENT != "prod":
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("db", "localhost", 1).replace(
        "5432", "5433"
    )
print(ASYNC_DATABASE_URL)

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

# keyword - CrawledKeyword 리스트의 딕셔너리
id_to_crawled_keyword: dict[Keyword, list[CrawledKeyword]] = {}


async def handle_keyword(
    keyword: Keyword,
) -> None:
    """
    단일 키워드를 크롤링하고 크롤링 결과를 id_to_crawled_keyword에 직접 저장
    """
    print(f"[INFO] 키워드 처리: {keyword.title}")

    # 함수 내부에서 세션 생성
    async with AsyncSessionLocal() as session:
        crawled_data: list[CrawledKeyword] = await get_new_hotdeal_keywords(
            session=session,
            keyword=keyword,
        )

        if crawled_data:
            id_to_crawled_keyword[keyword] = crawled_data
            print(
                f"[INFO] 키워드 처리: {keyword.title} 신규 핫딜 {len(crawled_data)}건 발견"
            )
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
            first_product = KeywordSite(
                keyword_id=keyword.id,
                site_name=SiteName.ALGUMON,
                external_id=product.id,
                link=product.link,
                price=product.price,
                meta_data=product.meta_data,
            )

        # 첫번째 프로덕트가 아니라면, 지금 프로덕트의 아이디와 기존 저장된 프로덕트 아이디가 같다면 return
        elif not is_first_product and result and result.external_id == product.id:
            result.external_id = first_product.external_id
            result.link = first_product.link
            result.price = first_product.price
            result.meta_data = first_product.meta_data
            result.wdate = datetime.now()
            await session.commit()
            return return_result

        return_result.append(product)
        is_first_product = False


async def job():
    """
    사용자와 연결된 키워드만 불러와 병렬로 처리하고, 결과를 취합하여 메일을 발송합니다.
    """
    PROXY_MANAGER.fetch_proxies()
    keywords_to_process: list[Keyword] = []
    all_users_with_keywords: list[User] = []  # 사용자 정보를 담을 리스트 추가

    try:
        async with AsyncSessionLocal() as session:
            # 사용자와 매핑된 키워드만 조회
            stmt = select(Keyword).where(Keyword.users.any())
            result = await session.execute(stmt)
            keywords_to_process = result.scalars().unique().all()

            # 메일 발송을 위해 모든 사용자 정보 미리 로드 (키워드 정보 포함)
            user_stmt = select(User).options(selectinload(User.keywords))
            user_result = await session.execute(user_stmt)
            all_users_with_keywords = user_result.scalars().unique().all()
    except Exception as e:
        logger.error(f"DB 조회 중 오류 발생: {e}")
        return  # DB 조회 실패 시 작업 중단

    if not keywords_to_process:
        print("[INFO] 처리할 활성 키워드가 없습니다.")
        return

    PROXY_MANAGER.reset_proxies()
    tasks = [handle_keyword(kw) for kw in keywords_to_process]
    # return_exceptions=True 로 설정하여 개별 작업 실패가 전체를 중단시키지 않도록 함
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 개별 크롤링 작업 결과 확인 및 로깅
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            failed_keyword = keywords_to_process[i]
            logger.error(f"키워드 '{failed_keyword.title}' 처리 중 오류 발생: {res}")

    print("[INFO] 모든 키워드 크롤링 완료. 메일 발송 시작...")

    # 사용자별 메일 발송 로직
    for user in all_users_with_keywords:
        try:
            user_deals: dict[Keyword, list[CrawledKeyword]] = {}
            # 사용자가 구독한 Keyword 객체들을 set으로 만들어 빠른 조회를 지원
            subscribed_keywords_set = set(user.keywords)

            # 사용자가 구독한 키워드 중 크롤링된 결과가 있는지 확인
            for crawled_keyword_obj, deals in id_to_crawled_keyword.items():
                if crawled_keyword_obj in subscribed_keywords_set:
                    user_deals[crawled_keyword_obj] = deals

            if user_deals:
                # 메일 내용 생성
                email_content: str = ""
                subject: str = ""
                for keyword, deals in user_deals.items():
                    try:
                        email_content += await make_hotdeal_email_content(
                            keyword, deals
                        )
                        subject += f"{keyword.title}, "
                    except Exception as e:
                        logger.error(
                            f"사용자 {user.email}, 키워드 {keyword.title} 메일 내용 생성 중 오류: {e}"
                        )
                        # 내용 생성 실패 시 해당 키워드는 건너뛰고 계속 진행
                        continue

                if not email_content:
                    # 모든 키워드에서 내용 생성 실패 시 메일 발송 안함
                    print(
                        f"[INFO] 사용자 {user.email} 에게 발송할 유효한 메일 내용 없음"
                    )
                    continue

                subject = subject.rstrip(", ")  # 마지막 쉼표 및 공백 제거
                subject = f"[{subject}] 새로운 핫딜 알림"

                if settings.ENVIRONMENT == "prod":
                    await send_email(
                        subject=subject,
                        to=user.email,
                        body=email_content,
                        is_html=True,
                    )
                    # 메일 발송 성공 로그 (선택적)
                    # logger.info(f"사용자 {user.email} 에게 메일 발송 완료.")
                else:
                    logger.info(
                        f"[DEV] 사용자 {user.email} 에게 메일 발송 제목:{subject} 내용:{email_content}"
                    )
            # else:
            # 발송할 딜 없는 경우 로그는 위에서 처리했으므로 주석처리 또는 제거
            # print(f"[INFO] 사용자 {user.email} 에게 발송할 새 핫딜 없음")
        except Exception as e:
            # 사용자별 메일 처리 루프 전체에서 예외 발생 시 로깅
            logger.error(f"사용자 {user.email} 메일 처리 중 오류 발생: {e}")
            # 다음 사용자로 계속 진행
            continue

    # 다음 스케줄링을 위해 크롤링 결과 초기화
    id_to_crawled_keyword.clear()
    print("[INFO] 메일 발송 완료 및 크롤링 결과 초기화")


def main():
    loop = asyncio.get_event_loop()  # 이벤트 루프를 가져오거나 생성합니다.
    scheduler = AsyncIOScheduler(
        timezone="Asia/Seoul", event_loop=loop
    )  # 스케줄러에 루프를 전달합니다.

    trigger = CronTrigger(minute="0,30")
    if settings.ENVIRONMENT != "prod":
        trigger = CronTrigger(minute="*")
    scheduler.add_job(
        job,
        trigger=trigger,
        id="hotdeal_worker",
        replace_existing=True,
    )

    scheduler.start()
    print("[INFO] Worker 스케줄러 시작: 매시 정각 및 30분마다 크롤링 및 메일 발송")

    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        print("[INFO] Worker 종료 중...")
        scheduler.shutdown()


if __name__ == "__main__":
    if settings.ENVIRONMENT == "prod":
        main()
    else:
        asyncio.run(job())
