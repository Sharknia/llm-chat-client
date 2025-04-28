from fastapi import status

from app.src.core.exceptions.base_exceptions import BaseHTTPException


class ClientErrors:
    # 키워드 갯수 초과
    KEYWORD_COUNT_OVERFLOW = BaseHTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Keyword count overflow",
        description="BAD REQUEST",
    )
