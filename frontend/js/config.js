// API Configuration
// Change this to your Render.com backend URL after deployment
const API_BASE_URL = window.location.hostname === 'localhost'
    ? ''
    : 'https://jobguard-ai-api.onrender.com';

/**
 * Make API request with base URL, timeout, and retry
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const timeout = options.timeout || 120000; // 2 min timeout (Render free tier is slow)

    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);

        if (error.name === 'AbortError') {
            throw new Error(
                'Request timed out. The server is taking too long to respond. ' +
                'Render free tier servers may be sleeping — please try again in 30 seconds.'
            );
        }

        if (error.message === 'Failed to fetch' || error instanceof TypeError) {
            throw new Error(
                'Cannot connect to the analysis server. This can happen when:\n' +
                '• The server is waking up (Render free tier sleeps after inactivity — wait 30-60 seconds and retry)\n' +
                '• The server is redeploying\n' +
                'Please wait a moment and try again.'
            );
        }

        throw error;
    }
}
