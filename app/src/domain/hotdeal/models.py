from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.src.core.database import Base


class Keyword(Base):
    __tablename__ = "hotdeal_keywords"
    __table_args__ = (UniqueConstraint("title", name="uq_keywords_title"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    link = Column(String, nullable=True)
    price = Column(String, nullable=True)
    meta_data = Column(Text, nullable=True)
    wdate = Column(DateTime, default=datetime.now(UTC), nullable=False)

    users = relationship("User", secondary="user_keywords", back_populates="keywords")
