import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# load_dotenv() 제거 (main.py에서 처리)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# URL 스키마 수정: postgresql:// -> postgresql+asyncpg://
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# echo=True는 개발 중에 SQL 쿼리를 로그로 출력합니다.
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)

# 비동기 세션 메이커 설정
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # 비동기 컨텍스트에서 필요할 수 있음
)

Base = declarative_base()


# FastAPI 의존성 주입용 비동기 함수
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            # async with 블록이 세션 close를 자동으로 처리합니다.
            pass
