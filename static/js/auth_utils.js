import { clearTokens, fetchWithAuth } from './auth.js';

/**
 * 로그인 상태를 확인하는 함수
 * @returns {Promise<boolean>} 로그인되어 있지 않으면 false, 로그인되어 있으면 true를 반환
 */
export async function checkLoginStatus() {
    try {
        const response = await fetchWithAuth('/api/user/v1/me');
        if (!response.ok) {
            return false;
        }
        return true;
    } catch (error) {
        console.error('인증 확인 실패:', error);
        return false;
    }
}

/**
 * 사용자 정보를 가져오는 함수
 * @returns {Promise<Object>} 사용자 정보 객체 또는 null
 */
export async function getUserInfo() {
    try {
        const response = await fetchWithAuth('/api/user/v1/me');
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
export async function logout() {
    try {
        const response = await fetchWithAuth('/api/user/v1/logout', {
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
