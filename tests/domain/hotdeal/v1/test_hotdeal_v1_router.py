import pytest
from fastapi import Response

from app.src.core.exceptions.client_exceptions import ClientErrors
from app.src.domain.hotdeal.schemas import KeywordResponse


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "request_data, expected_status, mock_side_effect, expected_response",
    [
        # 정상 요청
        (
            {
                "title": "Keyword",
            },
            201,
            None,
            {
                "title": "keyword",
            },
        ),
        # 키워드 갯수 초과
        (
            {
                "title": "Keyword",
            },
            ClientErrors.KEYWORD_COUNT_OVERFLOW.status_code,
            ClientErrors.KEYWORD_COUNT_OVERFLOW,
            {
                "description": ClientErrors.KEYWORD_COUNT_OVERFLOW.description,
                "detail": ClientErrors.KEYWORD_COUNT_OVERFLOW.detail,
            },
        ),
    ],
)
async def test_post_keyword(
    mocker,
    mock_client,
    mock_authenticated_user,
    override_registered_user,
    request_data,
    expected_status,
    mock_side_effect,
    expected_response,
):
    """키워드 등록 API 테스트"""
    # 테스트용 인증 유저 오버라이드
    override_registered_user(mock_authenticated_user)

    if mock_side_effect:
        mocker.patch(
            "app.src.domain.hotdeal.v1.router.register_keyword",
            side_effect=mock_side_effect,
        )
    else:
        mocker.patch(
            "app.src.domain.hotdeal.v1.router.register_keyword",
            return_value=KeywordResponse(title="keyword"),
        )

    # API 호출
    response: Response = mock_client.post("/api/hotdeal/v1/keywords", json=request_data)

    # 응답 검증
    assert response.status_code == expected_status

    if expected_response:
        assert response.json() == expected_response
    else:
        response_data = response.json()
        assert response_data["title"] == "keyword"
