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

export const API_URL = getApiUrl();
