function getApiUrl() {
    const hostname = window.location.hostname;
    const port = window.location.port;

    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        if (port === '8001') {
            return 'http://localhost:8001/api';
        } else if (port === '8000') {
            return 'http://localhost:8000/api';
        }
    } else if (hostname.includes('dev.')) {
        return 'https://dev-api.tuum.day/api';
    } else {
        return 'https://api.tuum.day/api';
    }
}

const API_URL = getApiUrl();

// 토큰 관리를 위한 키 상수
const TOKEN_KEYS = {
    ACCESS_TOKEN: 'access_token',
    USER_ID: 'user_id',
};

// 토큰 저장
function saveTokens(accessToken, userId) {
    sessionStorage.setItem(TOKEN_KEYS.ACCESS_TOKEN, accessToken);
    sessionStorage.setItem(TOKEN_KEYS.USER_ID, userId);
}

// 토큰 가져오기
function getTokens() {
    return {
        accessToken: sessionStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN),
        userId: sessionStorage.getItem(TOKEN_KEYS.USER_ID),
    };
}

// 토큰 삭제 (로그아웃 시 사용)
function clearTokens() {
    sessionStorage.removeItem(TOKEN_KEYS.ACCESS_TOKEN);
    sessionStorage.removeItem(TOKEN_KEYS.USER_ID);
}

// 토큰 존재 여부 확인
function hasValidTokens() {
    return !!sessionStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN);
}

// API 요청 시 사용할 인증 헤더 생성
function getAuthHeaders() {
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
    console.log('액세스 토큰 갱신 시도...');

    try {
        // 중요: 토큰 갱신 요청은 fetchWithAuth를 사용하지 않음 (무한 루프 방지)
        const refreshResponse = await fetch(`${API_URL}/user/v1/token/refresh`, {
            method: 'POST',
            credentials: 'include',
        });

        if (refreshResponse.ok) {
            const data = await refreshResponse.json();
            saveTokens(data.access_token, data.user_id);
            console.log('토큰 갱신 성공. 원래 요청 재시도:', originalUrl);
            return fetchWithAuth(originalUrl, originalOptions);
        } else {
            console.error('토큰 갱신 실패:', refreshResponse.status, await refreshResponse.text());
            forceLogout();
            return null;
        }
    } catch (error) {
        console.error('토큰 갱신 중 네트워크 오류 또는 기타 문제 발생:', error);
        forceLogout();
        return null;
    }
}

/**
 * 인증 헤더와 함께 fetch 요청을 보내는 공용 함수 (401 시 토큰 갱신 및 재시도)
 * @param {string} url 요청할 URL
 * @param {RequestInit} options fetch 옵션 객체
 * @returns {Promise<Response>} fetch Promise
 */
async function fetchWithAuth(url, options = {}) {
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
        credentials: 'include',
    };

    try {
        const full_url = API_URL + url;
        const response = await fetch(full_url, mergedOptions);

        // 401 Unauthorized 에러 발생 시 토큰 갱신 및 재시도 로직
        if (response.status === 401) {
            console.warn('[fetchWithAuth] 401 Unauthorized 감지. 토큰 갱신 및 재시도 시작... :' + full_url);
            // 재시도 함수의 결과를 반환 (성공 시 Response, 실패 시 null)
            const retryResponse = await refreshTokenAndRetry(url, mergedOptions);
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

/**
 * 로그인 상태를 확인하는 함수
 * @returns {Promise<boolean>} 로그인되어 있지 않으면 false, 로그인되어 있으면 true를 반환
 */
async function checkLoginStatus() {
    try {
        const response = await fetchWithAuth('/user/v1/me');
        return response.ok;
    } catch (error) {
        console.error('인증 확인 실패:', error);
        return false;
    }
}

/**
 * 사용자 정보를 가져오는 함수
 * @returns {Promise<Object>} 사용자 정보 객체 또는 null
 */
async function getUserInfo() {
    try {
        const response = await fetchWithAuth('/user/v1/me');
        if (!response.ok) {
            return null;
        }
        return await response.json();
    } catch (error) {
        console.error('사용자 정보 조회 실패:', error);
        return null;
    }
}

/**
 * 로그아웃 처리 함수
 * @returns {Promise<boolean>} 로그아웃 성공 여부
 */
async function logout() {
    try {
        const response = await fetchWithAuth('/user/v1/logout', {
            method: 'POST',
        });
        if (response.ok) {
            clearTokens();
            window.location.href = '/login';
            return true;
        }
        return false;
    } catch (error) {
        console.error('로그아웃 실패:', error);
        return false;
    }
}
