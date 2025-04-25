import { API_URL } from './config.js';

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

/**
 * 강제 로그아웃 및 로그인 페이지 리다이렉트 처리
 */
function forceLogout() {
    clearTokens();
    alert('세션이 만료되었거나 유효하지 않습니다. 다시 로그인해주세요.');
    window.location.href = '/login';
}

/**
 * 토큰을 갱신하고 원래 요청을 재시도하는 함수
 * @param {string} originalUrl 재시도할 원래 URL
 * @param {RequestInit} originalOptions 재시도할 원래 fetch 옵션
 * @returns {Promise<Response|null>} 재시도 성공 시 Response, 실패 시 null
 */
async function refreshTokenAndRetry(originalUrl, originalOptions) {
    const { refreshToken } = getTokens();

    if (!refreshToken) {
        console.error('리프레시 토큰 없음. 로그아웃 처리.');
        forceLogout();
        return null; // 재시도 불가
    }

    console.log('액세스 토큰 갱신 시도...');

    try {
        // 중요: 토큰 갱신 요청은 fetchWithAuth를 사용하지 않음 (무한 루프 방지)
        // 또한, 이 요청의 Authorization 헤더에는 리프레시 토큰을 사용해야 함.
        const refreshResponse = await fetch('/api/user/v1/token/refresh', {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${refreshToken}`,
                'Content-Type': 'application/json', // 필요시 추가
            },
            // body: JSON.stringify({}) // POST 요청 시 빈 바디라도 필요할 수 있음
        });

        if (refreshResponse.ok) {
            const data = await refreshResponse.json();
            saveTokens(data.access_token, data.refresh_token, data.user_id);
            console.log('토큰 갱신 성공. 원래 요청 재시도:', originalUrl);
            // 갱신된 토큰으로 원래 요청 재시도
            // 재시도 시에는 반드시 원래의 options 객체를 다시 전달해야 함
            return fetchWithAuth(originalUrl, originalOptions);
        } else {
            console.error('토큰 갱신 실패:', refreshResponse.status, await refreshResponse.text());
            forceLogout();
            return null; // 재시도 실패
        }
    } catch (error) {
        console.error('토큰 갱신 중 네트워크 오류 또는 기타 문제 발생:', error);
        forceLogout();
        return null; // 재시도 실패
    }
}

/**
 * 인증 헤더와 함께 fetch 요청을 보내는 공용 함수 (401 시 토큰 갱신 및 재시도)
 * @param {string} url 요청할 URL
 * @param {RequestInit} options fetch 옵션 객체
 * @returns {Promise<Response>} fetch Promise
 */
export async function fetchWithAuth(url, options = {}) {
    // 토큰이 없다면 로그인 페이지로 리다이렉트
    if (!hasValidTokens()) {
        window.location.href = '/login';
        return;
    }

    const headers = getAuthHeaders();

    // 기존 옵션의 헤더와 병합
    const mergedHeaders = {
        ...(options.headers || {}),
        ...headers,
    };
    // Content-Type은 body가 있을 때만 추가하는 것이 더 안전할 수 있음
    if (options.body && !(options.body instanceof FormData)) {
        mergedHeaders['Content-Type'] = 'application/json';
    }

    // options.body가 객체면 JSON 문자열로 변환 (FormData 제외)
    let body = options.body;
    if (typeof body === 'object' && body !== null && !(body instanceof FormData)) {
        body = JSON.stringify(body);
    }

    const mergedOptions = {
        ...options,
        headers: mergedHeaders,
        body: body,
    };

    try {
        url = API_URL + url;
        const response = await fetch(url, mergedOptions);

        // 401 Unauthorized 에러 발생 시 토큰 갱신 및 재시도 로직
        if (response.status === 401) {
            console.warn('401 Unauthorized 감지. 토큰 갱신 및 재시도 시작...');
            // 재시도 함수의 결과를 반환 (성공 시 Response, 실패 시 null)
            const retryResponse = await refreshTokenAndRetry(url, options);
            // 재시도 실패(null) 시 에러처럼 처리하거나, 호출 측에서 null을 처리하도록 함
            if (retryResponse === null) {
                // 이미 forceLogout이 호출되었으므로 여기서는 에러만 던져서 흐름 중단
                throw new Error('Token refresh failed and user was logged out.');
            }
            return retryResponse;
        } else {
            // 401이 아니면 정상 응답 반환
            return response;
        }
    } catch (error) {
        // 네트워크 에러 또는 재시도 실패 에러 처리
        console.error(`fetchWithAuth 실패 [${options.method || 'GET'} ${url}]:`, error);
        // 여기서 에러를 다시 던져서, 호출한 곳에서 처리하도록 함
        throw error;
    }
}
