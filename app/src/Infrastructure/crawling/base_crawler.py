from abc import ABC, abstractmethod

import requests

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

    def fetch(
        self,
        url: str = None,
        timeout: int = 10,
    ) -> str:
        """HTML 가져오기 (프록시 포함)."""
        target_url = url or self.url  # url이 명시되지 않으면 기본적으로 self.url 사용
        logger.info(f"요청: {target_url}")
        try:
            response = requests.get(
                target_url,
                timeout=timeout,
            )
            # 알구몬의 경우 오라클 클라우드 ip에 대해 403이 뜨고, FMKorea의 경우 잦은 요청에 대해 430이 발생하는 경우가 있어 예외처리
            if response.status_code == 403 or response.status_code == 430:
                # 430인 경우 에러 전체 내용을 출력한다.
                if response.status_code == 430:
                    logger.error(f"{response.status_code}: {response.text}")
                logger.warning(
                    f"{response.status_code}: 접근이 차단되었습니다. 프록시로 재시도합니다."
                )
                # 403이 발생하면 프록시를 사용하여 재시도
                return self._fetch_with_proxy(target_url, timeout)

            response.raise_for_status()
            logger.info(f"요청 성공: {target_url}")
            return response.text

        except requests.exceptions.RequestException as e:
            logger.error(f"요청 실패: {e}")
            return None

    def _fetch_with_proxy(
        self,
        url: str,
        timeout: int = 100,
    ):
        """프록시를 사용하여 HTML 가져오기."""
        for proxy in self.proxy_manager.proxies:
            try:
                response = requests.get(
                    url,
                    proxies={"http": proxy, "https": proxy},
                    timeout=timeout,
                )
                if response.status_code == 403 or response.status_code == 430:
                    logger.warning(f"프록시 {proxy}에서 {response.status_code} 발생")
                    continue  # 다음 프록시로 재시도
                elif response.status_code == 200:
                    logger.info(f"프록시 {proxy}로 요청 성공")
                    return response.text
            except requests.exceptions.RequestException:
                # 에러 전체 내용 기록
                logger.warning(f"프록시 {proxy}로 요청 실패")
        logger.error("모든 프록시를 사용했지만 요청에 실패했습니다.")
        return None

    def fetchparse(
        self,
    ) -> list[CrawledKeyword]:
        """크롤링 실행 (필요 시 오버라이드)."""
        html = self.fetch()
        if html:
            self.results = self.parse(html)
        else:
            logger.error(f"크롤링 실패: {self.url}")
        return self.results
