// 토큰 관리를 위한 키 상수
const TOKEN_KEYS = {
    ACCESS_TOKEN: 'access_token',
    REFRESH_TOKEN: 'refresh_token',
    USER_ID: 'user_id',
};

// 토큰 저장
export function saveTokens(accessToken, refreshToken, userId) {
    sessionStorage.setItem(TOKEN_KEYS.ACCESS_TOKEN, accessToken);
    sessionStorage.setItem(TOKEN_KEYS.REFRESH_TOKEN, refreshToken);
    sessionStorage.setItem(TOKEN_KEYS.USER_ID, userId);
}

// 토큰 가져오기
export function getTokens() {
    return {
        accessToken: sessionStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN),
        refreshToken: sessionStorage.getItem(TOKEN_KEYS.REFRESH_TOKEN),
        userId: sessionStorage.getItem(TOKEN_KEYS.USER_ID),
    };
}

// 토큰 삭제 (로그아웃 시 사용)
export function clearTokens() {
    sessionStorage.removeItem(TOKEN_KEYS.ACCESS_TOKEN);
    sessionStorage.removeItem(TOKEN_KEYS.REFRESH_TOKEN);
    sessionStorage.removeItem(TOKEN_KEYS.USER_ID);
}

// 토큰 존재 여부 확인
export function hasValidTokens() {
    return !!sessionStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN);
}

// API 요청 시 사용할 인증 헤더 생성
export function getAuthHeaders() {
    const accessToken = sessionStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN);
    return accessToken
        ? {
              Authorization: `Bearer ${accessToken}`,
          }
        : {};
}
