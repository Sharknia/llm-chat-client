from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """모의 AsyncSession 객체를 생성하는 픽스처"""
    session = AsyncMock(spec=AsyncSession)
    # execute 메서드의 반환 값 설정을 위해 mock_result 추가
    session.execute = AsyncMock()
    return session
