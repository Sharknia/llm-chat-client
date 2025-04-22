from collections.abc import AsyncGenerator

import pytest

# SQLAlchemy 비동기 관련 임포트 추가
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.src.core.database import Base
from app.src.core.security import hash_password
from app.src.domain.user.models import User

# SQLite 인메모리 데이터베이스 설정 (비동기)
# 참고: SQLite 비동기 드라이버 필요 (e.g., aiosqlite)
# poetry add aiosqlite 또는 pip install aiosqlite
ASYNC_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(
    ASYNC_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 비동기 세션 메이커 설정
# expire_on_commit=False 는 FastAPI에서 Depends(get_db) 패턴과 함께 사용할 때 권장됨
SessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture
async def mock_db_session() -> AsyncGenerator[AsyncSession, None]:
    """비동기 AsyncSession 객체를 생성하는 픽스처"""

    # 테이블 초기화 및 재생성 (비동기 방식)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # 비동기 세션 시작
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()  # 성공 시 커밋 (선택적)
        except Exception:
            await session.rollback()  # 실패 시 롤백
            raise
        finally:
            await session.close()


@pytest.fixture
async def add_mock_user(
    mock_db_session: AsyncSession,
):
    async def _add_mock_user(
        id: int = 1,
        email: str = "test@example.com",
        password: str = "password",
        is_active: bool = False,
    ) -> User:
        """
        테스트를 위한 mock user를 DB에 추가하는 함수
        """
        hashed_password = hash_password(password)
        user = User(
            id=id,
            email=email,
            password=hashed_password,
            is_active=is_active,
        )
        await mock_db_session.add(user)
        await mock_db_session.commit()
        return user

    return _add_mock_user
