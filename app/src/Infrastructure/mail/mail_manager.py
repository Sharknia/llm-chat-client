import smtplib
from email.mime.text import MIMEText

from app.src.core.config import settings
from app.src.core.logger import logger
from app.src.domain.hotdeal.models import Keyword
from app.src.domain.hotdeal.schemas import CrawledKeyword


async def make_hotdeal_email_content(
    keyword: Keyword,
    updates: list[CrawledKeyword],
) -> str:
    """
    핫딜 업데이트 내용을 메일 형식으로 변환
    """
    text = f"<h2><a href='https://www.algumon.com/search/{keyword.title}'>{keyword.title} 검색 결과</a></h2>"
    product_list_html = "".join(
        [
            f"<p><a href='{product.link}'>{product.title}</a> - {product.price}</p>"
            for product in updates
        ]
    )
    text += product_list_html
    return text


async def send_email(
    subject: str = "메일 제목",
    to: str = "zel@kakao.com",
    sender: str = "zel@kakao.com",
    body: str = None,
    is_html: str = False,
):
    try:
        msg = MIMEText(body, "html" if is_html else "plain")  # HTML 형식 지원
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to

        with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
            server.sendmail(
                sender,
                to,
                msg.as_string(),
            )

        # TODO: 메일 전송 로그 남기기
        logger.info("메일 전송 완료!")
    except Exception as e:
        logger.error(f"메일 전송 실패: {e}")
