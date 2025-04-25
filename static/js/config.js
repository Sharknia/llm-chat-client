function getApiUrl() {
    const hostname = window.location.hostname;
    const port = window.location.port;

    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        if (port === '8001') {
            return 'http://localhost:8001';
        } else if (port === '8000') {
            return 'http://localhost:8000';
        }
    } else if (hostname.includes('dev.')) {
        return 'https://dev-api.tuum.dev';
    } else {
        return 'https://api.tuum.dev';
    }
}

export const API_URL = getApiUrl();
