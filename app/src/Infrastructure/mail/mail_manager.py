import smtplib
from email.mime.text import MIMEText

from app.src.core.config import settings
from app.src.core.logger import logger
from app.src.domain.hotdeal.schemas import CrawledKeyword


class MailManager:
    def notify(
        self,
        keyword: str,
        updates: list[CrawledKeyword],
    ):
        subject = None
        text = f"<h2><a href='https://www.algumon.com/search/{keyword}'>전체 검색 결과</a></h2>"
        # 업데이트 모드에서 HTML 리스트 생성
        product_list_html = "".join(
            [
                f"<p><a href='{product.current_link}'>{product.current_title}</a> - {product.current_price}</p>"
                for product in updates
            ]
        )
        text += product_list_html  # 기존 텍스트에 리스트를 추가
        subject = f"[{keyword}] 새로운 핫딜 등장!"
        # TODO: 해당 키워드를 가진 유저들을 찾아서 그 유저들에게 메일 전송
        self.send_email(subject, text, is_html=True)
        logger.info("알림 완료!")

    def send_email(
        self,
        subject="메일 제목",
        to="zel@kakao.com",
        body=None,
        is_html=False,
    ):
        try:
            msg = MIMEText(body, "html" if is_html else "plain")  # HTML 형식 지원
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM
            msg["To"] = to

            with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
                server.sendmail(
                    settings.SMTP_FROM,
                    to,
                    msg.as_string(),
                )

            # TODO: 메일 전송 로그 남기기
            logger.info("메일 전송 완료!")
        except Exception as e:
            logger.error(f"메일 전송 실패: {e}")
