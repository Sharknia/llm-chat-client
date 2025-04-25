function getApiUrl() {
    const hostname = window.location.hostname;

    if (hostname.includes('http://localhost:8001/')) {
        return 'http://localhost:8001';
    } else if (hostname.includes('http://localhost:8000/')) {
        return 'http://localhost:8000';
    } else if (hostname.includes('dev.')) {
        return 'https://dev-api.tuum.dev';
    } else {
        return 'https://api.tuum.dev';
    }
}

export const API_URL = getApiUrl();
