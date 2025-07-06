import requests
from bs4 import BeautifulSoup

from app.src.core.logger import logger


class ProxyManager:
    """싱글톤 프록시 관리자."""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ProxyManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, proxy_url="https://www.sslproxies.org/"):
        if ProxyManager._initialized:
            return
        self.proxy_url = proxy_url
        self.proxies = []
        ProxyManager._initialized = True

    def fetch_proxies(self):
        """무료 프록시를 수집하여 저장."""
        try:
            response = requests.get(self.proxy_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            table = soup.find("table", {"class": "table table-striped table-bordered"})

            if not table:
                logger.warning("프록시 테이블을 찾을 수 없습니다.")
                return []

            rows = table.find("tbody").find_all("tr")
            self.proxies = [
                f"http://{row.find_all('td')[0].text.strip()}:{row.find_all('td')[1].text.strip()}"
                for row in rows
                if row.find_all("td")[6].text.strip().lower() == "yes"
                and row.find_all("td")[4].text.strip().lower() == "anonymous"
            ][:15]

            if self.proxies:
                logger.info(f"프록시 설정 완료: {self.proxies}")
            else:
                logger.warning("HTTPS 지원 및 익명 프록시를 찾지 못했습니다.")

        except Exception as e:
            logger.error(f"프록시 가져오기 실패: {e}")
        return self.proxies

    def reset_proxies(self):
        """프록시 리스트 초기화."""
        self.proxies = []
        logger.info("프록시 리스트 초기화 완료")

    def remove_proxy(self, proxy_url: str):
        """특정 프록시를 리스트에서 안전하게 제거."""
        try:
            self.proxies.remove(proxy_url)
            logger.info(f"프록시 제거됨: {proxy_url}")
        except ValueError:
            # 다른 작업에 의해 이미 제거된 경우, 조용히 넘어감
            pass
