from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.src.core.database import Base
from app.src.domain.hotdeal.enums import SiteName


class Keyword(Base):
    __tablename__ = "hotdeal_keywords"
    __table_args__ = (UniqueConstraint("title", name="uq_keywords_title"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    wdate = Column(DateTime, default=datetime.now(UTC), nullable=False)

    users = relationship("User", secondary="user_keywords", back_populates="keywords")
    mail_logs = relationship("MailLog", back_populates="keyword")


class KeywordSite(Base):
    __tablename__ = "hotdeal_keyword_sites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword_id = Column(Integer, ForeignKey("hotdeal_keywords.id"), nullable=False)
    site_name = Column(Enum(SiteName), nullable=False, default=SiteName.ALGUMON)
    external_id = Column(String, nullable=False)
    link = Column(String, nullable=True)
    price = Column(String, nullable=True)
    meta_data = Column(Text, nullable=True)
    wdate = Column(DateTime, default=datetime.now(UTC), nullable=False)
