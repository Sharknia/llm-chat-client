from abc import ABC, abstractmethod

import httpx

from app.src.core.logger import logger
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.src.Infrastructure.crawling.proxy_manager import ProxyManager


class BaseCrawler(ABC):
    """크롤러의 기본 추상 클래스."""

    def __init__(
        self,
        keyword: str,
    ):
        self.keyword = keyword
        self.proxy_manager: ProxyManager = ProxyManager()
        self.results = []

    @property
    @abstractmethod
    def url(
        self,
    ) -> str:
        """크롤링 대상 URL (하위 클래스에서 구현 필수)."""
        pass

    @abstractmethod
    def parse(
        self,
        html: str,
    ) -> list[CrawledKeyword]:
        """파싱 로직 (사이트별 구현 필요)."""
        pass

    async def fetch(
        self,
        url: str = None,
        timeout: int = 10,
    ) -> str | None:
        """HTML 가져오기 (프록시 포함)."""
        target_url = url or self.url
        logger.info(f"요청: {target_url}")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(target_url, timeout=timeout)

                if response.status_code in [403, 430]:
                    if response.status_code == 430:
                        logger.error(f"{response.status_code}: {response.text}")
                    logger.warning(
                        f"{response.status_code}: 접근이 차단되었습니다. 프록시로 재시도합니다."
                    )
                    return await self._fetch_with_proxy(client, target_url, timeout)

                response.raise_for_status()
                logger.info(f"요청 성공: {target_url}")
                return response.text

            except httpx.RequestError as e:
                logger.error(f"요청 실패: {e}")
                return None

    async def _fetch_with_proxy(
        self,
        client: httpx.AsyncClient,
        url: str,
        timeout: int = 100,
    ) -> str | None:
        """프록시를 사용하여 HTML 가져오기."""
        for proxy in self.proxy_manager.proxies:
            try:
                proxies = {"http://": proxy, "https://": proxy}
                response = await client.get(url, proxies=proxies, timeout=timeout)

                if response.status_code in [403, 430]:
                    logger.warning(f"프록시 {proxy}에서 {response.status_code} 발생")
                    continue
                elif response.status_code == 200:
                    logger.info(f"프록시 {proxy}로 요청 성공")
                    return response.text
            except httpx.RequestError:
                logger.warning(f"프록시 {proxy}로 요청 실패")
        logger.error("모든 프록시를 사용했지만 요청에 실패했습니다.")
        return None

    async def fetchparse(
        self,
    ) -> list[CrawledKeyword]:
        """크롤링 실행 (필요 시 오버라이드)."""
        html = await self.fetch()
        if html:
            self.results = self.parse(html)
        else:
            logger.error(f"크롤링 실패: {self.url}")
        return self.results
