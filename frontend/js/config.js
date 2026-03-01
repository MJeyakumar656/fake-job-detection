// API Configuration
// 🚇 Cloudflare Tunnel — points to your local laptop. Run cloudflared first!
const API_BASE_URL = window.location.hostname === 'localhost'
    ? ''
    : 'https://monte-only-immediate-fell.trycloudflare.com';


/**
 * Make API request with base URL, timeout, and retry
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const timeout = options.timeout || 60000; // 60 second timeout (local machine is fast)

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
                'Render free tier servers may be sleeping — please try again in 60-120 seconds.'
            );
        }

        if (error.message === 'Failed to fetch' || error instanceof TypeError) {
            throw new Error(
                'Cannot connect. Make sure:\n' +
                '• Your laptop is on and python app.py is running\n' +
                '• cloudflared tunnel is running in a separate terminal'
            );
        }

        throw error;
    }
}
