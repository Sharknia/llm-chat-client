import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.sql.selectable import Select

# 테스트 대상 모듈 및 객체 임포트
from app.src.domain.user import repositories
from app.src.domain.user.enums import AuthLevel
from app.src.domain.user.models import User

# --- Fixtures ---


@pytest.fixture
def test_user_data() -> dict:
    """테스트용 사용자 데이터"""
    return {
        "id": uuid.uuid4(),
        "nickname": "testuser",
        "email": "test@example.com",
        "hashed_password": "fakehashedpassword",
        "auth_level": AuthLevel.USER,
        "is_active": False,
    }


@pytest.fixture
def mock_user(test_user_data) -> User:
    """모의 User 객체 생성"""
    # 실제 User 객체 대신 MagicMock 사용 가능 (테스트 복잡도에 따라)
    # 여기서는 간단히 User 객체 생성
    return User(**test_user_data)


# --- 테스트 함수 ---


@pytest.mark.asyncio
async def test_create_user(mock_db_session: AsyncMock, test_user_data):
    """create_user 함수 테스트"""
    # 함수 호출
    created_user = await repositories.create_user(
        db=mock_db_session,
        nickname=test_user_data["nickname"],
        email=test_user_data["email"],
        hashed_password=test_user_data["hashed_password"],
        auth_level=test_user_data["auth_level"],
        is_active=test_user_data["is_active"],
    )

    # 검증
    mock_db_session.add.assert_called_once()  # add 호출 확인
    mock_db_session.commit.assert_awaited_once()  # commit 호출 확인
    mock_db_session.refresh.assert_awaited_once()  # refresh 호출 확인

    # 생성된 사용자 속성 검증 (commit/refresh 후 반환된 객체 기준)
    assert created_user.nickname == test_user_data["nickname"]
    assert created_user.email == test_user_data["email"]
    assert created_user.auth_level == test_user_data["auth_level"]
    # User 모델이 실제 객체이므로, 생성 시 할당되지 않은 id, created_at 등은 검증 어려움
    # mock_db_session.refresh 호출 시 인자로 전달된 객체 검증이 더 정확할 수 있음
    added_user = mock_db_session.add.call_args[0][0]
    assert isinstance(added_user, User)
    assert added_user.nickname == test_user_data["nickname"]


@pytest.mark.asyncio
async def test_get_user_by_nickname(mock_db_session: AsyncMock, mock_user: User):
    """get_user_by_nickname 함수 테스트 (사용자 발견)"""
    # mock_result 설정
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db_session.execute.return_value = mock_result

    # 함수 호출
    found_user = await repositories.get_user_by_nickname(
        mock_db_session, mock_user.nickname
    )

    # 검증
    mock_db_session.execute.assert_awaited_once()  # execute 호출 확인
    assert found_user == mock_user
    # execute에 전달된 select 구문 검증 (더 상세하게)
    call_args = mock_db_session.execute.call_args[0]
    assert isinstance(call_args[0], Select)  # 비교 대상을 Select 타입으로 수정


@pytest.mark.asyncio
async def test_get_user_by_nickname_not_found(mock_db_session: AsyncMock):
    """get_user_by_nickname 함수 테스트 (사용자 없음)"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    found_user = await repositories.get_user_by_nickname(mock_db_session, "nonexistent")

    mock_db_session.execute.assert_awaited_once()
    assert found_user is None


@pytest.mark.asyncio
async def test_get_user_by_email(mock_db_session: AsyncMock, mock_user: User):
    """get_user_by_email 함수 테스트"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db_session.execute.return_value = mock_result

    found_user = await repositories.get_user_by_email(mock_db_session, mock_user.email)

    mock_db_session.execute.assert_awaited_once()
    assert found_user == mock_user


# ... (get_user_by_id 테스트 유사하게 추가) ...


@pytest.mark.asyncio
async def test_activate_user_success(mock_db_session: AsyncMock, mock_user: User):
    """activate_user 함수 테스트 (성공 케이스)"""
    mock_user.is_active = False  # 테스트를 위해 비활성 상태로 설정

    # get_user_by_id 모킹 (activate_user 내부에서 호출됨)
    # 여기서는 patch를 사용하거나, mock_db_session.execute를 두 번 설정
    mock_result_get = MagicMock()
    mock_result_get.scalar_one_or_none.return_value = mock_user

    # update 모킹
    mock_result_update = MagicMock()
    # update().returning() 이 scalar_one_or_none()으로 업데이트된 객체 반환 모방
    # 복사본 생성 시 필요한 속성만 명시적으로 전달
    updated_user_mock = User(
        id=mock_user.id,
        nickname=mock_user.nickname,
        email=mock_user.email,
        hashed_password=mock_user.hashed_password,
        auth_level=mock_user.auth_level,
        is_active=True,  # 업데이트된 값
        # created_at, updated_at 등은 테스트에 불필요하면 생략 가능
    )
    mock_result_update.scalar_one_or_none.return_value = updated_user_mock

    # execute가 호출 순서에 따라 다른 결과 반환하도록 설정
    mock_db_session.execute.side_effect = [mock_result_get, mock_result_update]

    activated_user = await repositories.activate_user(mock_db_session, mock_user.id)

    assert mock_db_session.execute.call_count == 2  # get_user + update
    mock_db_session.commit.assert_awaited_once()
    assert activated_user is not None
    assert activated_user.is_active is True


@pytest.mark.asyncio
async def test_activate_user_already_active(
    mock_db_session: AsyncMock, mock_user: User
):
    """activate_user 함수 테스트 (이미 활성 상태)"""
    mock_user.is_active = True

    mock_result_get = MagicMock()
    mock_result_get.scalar_one_or_none.return_value = mock_user
    mock_db_session.execute.return_value = mock_result_get  # get만 실행됨

    activated_user = await repositories.activate_user(mock_db_session, mock_user.id)

    mock_db_session.execute.assert_awaited_once()  # get_user만 호출
    mock_db_session.commit.assert_not_awaited()  # commit 호출 안 됨
    assert activated_user == mock_user  # 원래 사용자 객체 반환
    assert activated_user.is_active is True


# ... (update_user_auth_level, update_user_password 테스트 유사하게 추가) ...


@pytest.mark.asyncio
async def test_get_inactive_users(mock_db_session: AsyncMock, mock_user: User):
    """get_inactive_users 함수 테스트"""
    mock_user.is_active = False
    inactive_users_list = [mock_user]

    mock_result = MagicMock()
    mock_scalars_result = MagicMock()
    mock_scalars_result.all.return_value = inactive_users_list
    mock_result.scalars.return_value = mock_scalars_result
    mock_db_session.execute.return_value = mock_result

    users = await repositories.get_inactive_users(mock_db_session, skip=0, limit=10)

    mock_db_session.execute.assert_awaited_once()
    # 상세 필터 조건 검증 (~User.is_active)은 더 복잡한 mock 설정 필요
    assert users == inactive_users_list


# ... (get_all_users, get_user_auth_level 테스트 유사하게 추가) ...
