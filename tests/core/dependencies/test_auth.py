from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession  # AsyncSession 임포트 (모킹용)

from app.src.core.config import (
    settings,  # 설정값 (SECRET_KEY, REFRESH_TOKEN_SECRET_KEY)
)

# 테스트 대상 함수 및 관련 모듈 임포트
from app.src.core.dependencies.auth import (
    ALGORITHM,
    authenticate_admin_user,  # authenticate_admin_user 임포트 추가
    authenticate_user,  # authenticate_user 임포트 추가
    create_access_token,
    create_refresh_token,  # create_refresh_token 추가
    registered_user,  # registered_user 임포트 추가
)
from app.src.core.exceptions.auth_excptions import AuthErrors  # AuthErrors 임포트 추가
from app.src.domain.user.enums import AuthLevel  # AuthLevel Enum
from app.src.domain.user.schemas import (
    AuthenticatedUser,  # AuthenticatedUser 스키마 임포트
)


# pytest-asyncio 데코레이터
@pytest.mark.asyncio
async def test_create_access_token():
    """
    create_access_token 함수가 올바른 페이로드로 액세스 토큰을 생성하는지 테스트
    """
    # 테스트 데이터
    test_user_id = 1
    test_email = "test@example.com"
    test_auth_level = AuthLevel.USER
    expires_delta = timedelta(minutes=15)

    # 액세스 토큰 생성
    token = await create_access_token(
        user_id=test_user_id,
        email=test_email,
        auth_level=test_auth_level,
        expires_delta=expires_delta,
    )

    # 생성된 토큰 디코딩 (검증 포함)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

    # 페이로드 내용 검증
    assert payload.get("user_id") == test_user_id
    assert payload.get("email") == test_email
    assert (
        payload.get("auth_level") == test_auth_level.value
    )  # Enum 값으로 저장되었는지 확인
    assert "exp" in payload  # 만료 시간 필드 존재 여부 확인

    # 만료 시간 검증 (대략적으로 확인)
    exp_timestamp = payload.get("exp")
    expected_exp = datetime.now(UTC) + expires_delta
    # 생성/검증 시간차를 고려하여 약간의 오차 허용 (e.g., 60초)
    assert abs(datetime.fromtimestamp(exp_timestamp, UTC) - expected_exp) < timedelta(
        seconds=60
    )


@pytest.mark.asyncio
async def test_create_refresh_token():
    """
    create_refresh_token 함수가 올바른 페이로드로 토큰을 생성하고,
    save_refresh_token을 호출하는지 테스트
    """
    # 테스트 데이터
    test_user_id = 1
    test_email = "refresh@example.com"
    expires_delta = timedelta(days=7)

    # DB 세션 모킹
    mock_db = AsyncMock(spec=AsyncSession)

    # save_refresh_token 함수 모킹 (auth 모듈 내에서 참조되는 경로)
    with patch("app.src.core.dependencies.auth.save_refresh_token") as mock_save_token:
        # 리프레시 토큰 생성
        token = await create_refresh_token(
            db=mock_db,
            user_id=test_user_id,
            email=test_email,
            expires_delta=expires_delta,
        )

        # 생성된 토큰 디코딩 (검증 포함)
        payload = jwt.decode(
            token,
            settings.REFRESH_TOKEN_SECRET_KEY,  # 리프레시 토큰 키 사용
            algorithms=[ALGORITHM],
        )

        # 페이로드 내용 검증
        assert payload.get("user_id") == test_user_id
        assert payload.get("email") == test_email
        assert "exp" in payload  # 만료 시간 필드 존재 여부 확인
        # 리프레시 토큰에는 auth_level이 포함되지 않음 (선택사항)
        assert "auth_level" not in payload

        # 만료 시간 검증 (대략적으로 확인)
        exp_timestamp = payload.get("exp")
        expected_exp = datetime.now(UTC) + expires_delta
        assert abs(
            datetime.fromtimestamp(exp_timestamp, UTC) - expected_exp
        ) < timedelta(seconds=60)

        # save_refresh_token 호출 검증
        mock_save_token.assert_awaited_once_with(mock_db, test_user_id, token)


# ---- registered_user 테스트 시작 ----


@pytest.mark.asyncio
async def test_registered_user_valid_token():
    """
    registered_user: 유효한 액세스 토큰이 주어졌을 때 AuthenticatedUser를 반환하는지 테스트
    """
    test_user_id = 1
    test_email = "registered@example.com"
    test_auth_level = AuthLevel.USER

    # 테스트용 유효한 액세스 토큰 생성
    valid_token = await create_access_token(
        user_id=test_user_id, email=test_email, auth_level=test_auth_level
    )
    auth_header = f"Bearer {valid_token}"

    # registered_user 함수 호출
    authenticated_user = await registered_user(authorization=auth_header)

    # 반환된 객체 검증
    assert isinstance(authenticated_user, AuthenticatedUser)
    assert authenticated_user.user_id == test_user_id
    assert authenticated_user.email == test_email
    assert authenticated_user.auth_level == test_auth_level


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "auth_header, expected_exception",
    [
        (None, AuthErrors.INVALID_TOKEN),  # 헤더 없음
        ("Token invalid-token", AuthErrors.INVALID_TOKEN),  # 'Bearer ' 접두사 없음
        ("Bearer invalid-token-format", AuthErrors.INVALID_TOKEN),  # 잘못된 토큰 형식
        # 잘못된 키로 서명된 토큰 생성 (다른 키 사용)
        (
            f"Bearer {jwt.encode({'user_id': 1, 'email': 'e', 'auth_level': 1}, 'wrong-secret', algorithm=ALGORITHM)}",
            AuthErrors.INVALID_TOKEN,
        ),
        # 필수 페이로드 누락 케이스
        (
            f"Bearer {jwt.encode({'email': 'e', 'auth_level': 1, 'exp': datetime.now(UTC) + timedelta(minutes=5)}, settings.SECRET_KEY, algorithm=ALGORITHM)}",  # user_id 누락
            AuthErrors.INVALID_TOKEN_PAYLOAD,
        ),
        (
            f"Bearer {jwt.encode({'user_id': 1, 'auth_level': 1, 'exp': datetime.now(UTC) + timedelta(minutes=5)}, settings.SECRET_KEY, algorithm=ALGORITHM)}",  # email 누락
            AuthErrors.INVALID_TOKEN_PAYLOAD,
        ),
        (
            f"Bearer {jwt.encode({'user_id': 1, 'email': 'e', 'exp': datetime.now(UTC) + timedelta(minutes=5)}, settings.SECRET_KEY, algorithm=ALGORITHM)}",  # auth_level 누락
            AuthErrors.INVALID_TOKEN_PAYLOAD,
        ),
        # 잘못된 auth_level 값 케이스 (Enum에 없는 값)
        (
            f"Bearer {jwt.encode({'user_id': 1, 'email': 'e', 'auth_level': 99, 'exp': datetime.now(UTC) + timedelta(minutes=5)}, settings.SECRET_KEY, algorithm=ALGORITHM)}",
            AuthErrors.INVALID_TOKEN_PAYLOAD,
        ),
    ],
)
async def test_registered_user_invalid_cases(auth_header, expected_exception):
    """
    registered_user: 다양한 잘못된 토큰/헤더 케이스에서 적절한 예외를 발생시키는지 테스트
    """
    with pytest.raises(expected_exception.__class__) as exc_info:
        await registered_user(authorization=auth_header)
    assert exc_info.value.detail == expected_exception.detail


# ---- registered_user 테스트 끝 ----

# ---- authenticate_user 테스트 시작 ----


# 공통 테스트 데이터 및 토큰 생성 헬퍼 함수
async def create_test_token(
    user_id: int, email: str, level: AuthLevel, minutes_valid: int = 15
) -> str:
    return await create_access_token(
        user_id=user_id,
        email=email,
        auth_level=level,
        expires_delta=timedelta(minutes=minutes_valid),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("test_level", [AuthLevel.USER, AuthLevel.ADMIN])
async def test_authenticate_user_valid(test_level):
    """
    authenticate_user: 유효한 토큰과 활성 사용자(USER 또는 ADMIN)일 때 성공하는지 테스트
    """
    test_user_id = 2
    test_email = f"{test_level.name.lower()}@example.com"
    valid_token = await create_test_token(test_user_id, test_email, test_level)
    auth_header = f"Bearer {valid_token}"

    # DB 및 리포지토리 함수 모킹
    mock_db = AsyncMock(spec=AsyncSession)
    with patch(
        "app.src.core.dependencies.auth.check_user_active", return_value=True
    ) as mock_check_active:
        authenticated_user = await authenticate_user(
            db=mock_db, authorization=auth_header
        )

        # 결과 검증
        assert isinstance(authenticated_user, AuthenticatedUser)
        assert authenticated_user.user_id == test_user_id
        assert authenticated_user.email == test_email
        assert authenticated_user.auth_level == test_level

        # 모킹 함수 호출 검증
        mock_check_active.assert_awaited_once_with(mock_db, test_user_id)


@pytest.mark.asyncio
async def test_authenticate_user_inactive():
    """
    authenticate_user: 사용자가 활성 상태가 아닐 때 USER_NOT_ACTIVE 예외 발생하는지 테스트
    """
    test_user_id = 3
    test_email = "inactive@example.com"
    test_level = AuthLevel.USER
    valid_token = await create_test_token(test_user_id, test_email, test_level)
    auth_header = f"Bearer {valid_token}"

    # DB 및 리포지토리 함수 모킹 (check_user_active가 False 반환)
    mock_db = AsyncMock(spec=AsyncSession)
    with patch(
        "app.src.core.dependencies.auth.check_user_active", return_value=False
    ) as mock_check_active:
        with pytest.raises(AuthErrors.USER_NOT_ACTIVE.__class__) as exc_info:
            await authenticate_user(db=mock_db, authorization=auth_header)
        assert exc_info.value.detail == AuthErrors.USER_NOT_ACTIVE.detail
        mock_check_active.assert_awaited_once_with(mock_db, test_user_id)


@pytest.mark.asyncio
async def test_authenticate_user_expired_token():
    """
    authenticate_user: 만료된 토큰으로 ACCESS_TOKEN_EXPIRED 예외 발생하는지 테스트
    """
    test_user_id = 4
    test_email = "expired@example.com"
    test_level = AuthLevel.USER
    expired_token = await create_test_token(
        test_user_id, test_email, test_level, minutes_valid=-5
    )  # 5분 전에 만료된 토큰
    auth_header = f"Bearer {expired_token}"
    mock_db = AsyncMock(spec=AsyncSession)

    with pytest.raises(AuthErrors.ACCESS_TOKEN_EXPIRED.__class__) as exc_info:
        await authenticate_user(db=mock_db, authorization=auth_header)
    assert exc_info.value.detail == AuthErrors.ACCESS_TOKEN_EXPIRED.detail


# authenticate_user에 대한 다른 잘못된 토큰/헤더 케이스 (registered_user와 유사하나 DB 모킹 포함)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "auth_header, expected_exception",
    [
        (
            None,
            AuthErrors.NOT_AUTHENTICATED,
        ),  # 헤더 없음 (authenticate_user는 다른 예외 발생)
        (
            "Token invalid-token",
            AuthErrors.NOT_AUTHENTICATED,
        ),  # Bearer 없음 (authenticate_user는 다른 예외 발생)
        ("Bearer invalid-token-format", AuthErrors.INVALID_TOKEN),  # 잘못된 토큰 형식
        (
            f"Bearer {jwt.encode({'user_id': 1, 'email': 'e', 'auth_level': 1}, 'wrong-secret', algorithm=ALGORITHM)}",
            AuthErrors.INVALID_TOKEN,  # 잘못된 키
        ),
        (
            f"Bearer {jwt.encode({'email': 'e', 'auth_level': 1, 'exp': datetime.now(UTC) + timedelta(minutes=5)}, settings.SECRET_KEY, algorithm=ALGORITHM)}",
            AuthErrors.INVALID_TOKEN_PAYLOAD,  # user_id 누락
        ),
        # 추가적인 페이로드 오류 케이스는 registered_user 테스트에서 커버됨
    ],
)
async def test_authenticate_user_invalid_token_cases(auth_header, expected_exception):
    """
    authenticate_user: 잘못된 토큰/헤더 케이스에서 적절한 예외 발생하는지 테스트
    """
    mock_db = AsyncMock(spec=AsyncSession)
    # check_user_active 모킹은 여기서는 필요 없을 수 있음 (그 전에 예외 발생하므로)
    with patch("app.src.core.dependencies.auth.check_user_active", return_value=True):
        with pytest.raises(expected_exception.__class__) as exc_info:
            await authenticate_user(db=mock_db, authorization=auth_header)
        assert exc_info.value.detail == expected_exception.detail


# ---- authenticate_user 테스트 끝 ----

# ---- authenticate_admin_user 테스트 시작 ----


@pytest.mark.asyncio
async def test_authenticate_admin_user_valid():
    """
    authenticate_admin_user: 유효한 토큰과 활성 관리자(ADMIN)일 때 성공하는지 테스트
    """
    test_user_id = 10
    test_email = "admin@example.com"
    test_level = AuthLevel.ADMIN
    valid_token = await create_test_token(test_user_id, test_email, test_level)
    auth_header = f"Bearer {valid_token}"

    mock_db = AsyncMock(spec=AsyncSession)
    with patch(
        "app.src.core.dependencies.auth.check_user_active", return_value=True
    ) as mock_check_active:
        authenticated_user = await authenticate_admin_user(
            db=mock_db, authorization=auth_header
        )

        assert isinstance(authenticated_user, AuthenticatedUser)
        assert authenticated_user.user_id == test_user_id
        assert authenticated_user.email == test_email
        assert authenticated_user.auth_level == test_level
        mock_check_active.assert_awaited_once_with(mock_db, test_user_id)


@pytest.mark.asyncio
async def test_authenticate_admin_user_insufficient_permissions():
    """
    authenticate_admin_user: 일반 사용자(USER) 토큰으로 INSUFFICIENT_PERMISSIONS 예외 발생하는지 테스트
    """
    test_user_id = 11
    test_email = "user_for_admin_test@example.com"
    test_level = AuthLevel.USER  # 일반 사용자 레벨
    valid_token = await create_test_token(test_user_id, test_email, test_level)
    auth_header = f"Bearer {valid_token}"

    mock_db = AsyncMock(spec=AsyncSession)
    with patch(
        "app.src.core.dependencies.auth.check_user_active", return_value=True
    ) as mock_check_active:
        with pytest.raises(AuthErrors.INSUFFICIENT_PERMISSIONS.__class__) as exc_info:
            await authenticate_admin_user(db=mock_db, authorization=auth_header)
        assert exc_info.value.detail == AuthErrors.INSUFFICIENT_PERMISSIONS.detail
        # 권한 검사 전에 활성 상태를 확인하므로 check_user_active는 호출됨
        mock_check_active.assert_awaited_once_with(mock_db, test_user_id)


@pytest.mark.asyncio
async def test_authenticate_admin_user_inactive():
    """
    authenticate_admin_user: 관리자이지만 활성 상태가 아닐 때 USER_NOT_ACTIVE 예외 발생하는지 테스트
    """
    test_user_id = 12
    test_email = "inactive_admin@example.com"
    test_level = AuthLevel.ADMIN
    valid_token = await create_test_token(test_user_id, test_email, test_level)
    auth_header = f"Bearer {valid_token}"

    mock_db = AsyncMock(spec=AsyncSession)
    with patch(
        "app.src.core.dependencies.auth.check_user_active", return_value=False
    ) as mock_check_active:
        with pytest.raises(AuthErrors.USER_NOT_ACTIVE.__class__) as exc_info:
            await authenticate_admin_user(db=mock_db, authorization=auth_header)
        assert exc_info.value.detail == AuthErrors.USER_NOT_ACTIVE.detail
        mock_check_active.assert_awaited_once_with(mock_db, test_user_id)


# authenticate_admin_user에 대한 다른 잘못된 토큰/헤더 케이스는
# authenticate_user와 동일한 방식으로 처리되므로 생략 가능 (또는 필요한 경우 추가)

# ---- authenticate_admin_user 테스트 끝 ----
