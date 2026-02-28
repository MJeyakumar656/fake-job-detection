// API Configuration
// Change this to your Render.com backend URL after deployment
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? '' 
    : 'https://your-app-name.onrender.com';

/**
 * Make API request with base URL
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    return fetch(url, options);
}
