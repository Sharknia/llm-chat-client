from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import relationship

from app.src.core.database import Base


class MailLog(Base):
    __tablename__ = "mail_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sent_at = Column(DateTime, default=datetime.now(UTC), nullable=False)
    user = relationship("User", back_populates="mail_log")
    keyword = relationship("Keyword", back_populates="mail_log")
