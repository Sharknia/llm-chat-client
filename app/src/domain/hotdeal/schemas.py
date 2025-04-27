from datetime import datetime

from pydantic import BaseModel


class CrawledKeyword(BaseModel):
    id: str | None = None
    title: str | None = None
    link: str | None = None
    price: str | None = None
    meta_data: str | None = None
    wdate: str = datetime.now().isoformat()
