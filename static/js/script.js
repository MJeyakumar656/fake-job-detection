// ==================== DOM ELEMENTS ====================
const analyzeForm = document.getElementById('analyzeForm');
const jobInput = document.getElementById('jobInput');
const inputLabel = document.getElementById('inputLabel');
const analyzeBtn = document.getElementById('analyzeBtn');
const loadingState = document.getElementById('loadingState');
const errorMessage = document.getElementById('errorMessage');
const toggleBtns = document.querySelectorAll('.toggle-btn');

let currentInputType = 'url';

// ==================== EVENT LISTENERS ====================

// Input type toggle
toggleBtns.forEach(btn => {
    btn.addEventListener('click', function() {
        // Update active state
        toggleBtns.forEach(b => b.classList.remove('active'));
        this.classList.add('active');

        // Update input type and label
        currentInputType = this.dataset.type;
        
        if (currentInputType === 'url') {
            inputLabel.textContent = 'Paste Job URL:';
            jobInput.placeholder = 'https://www.linkedin.com/jobs/view/...';
        } else {
            inputLabel.textContent = 'Paste Job Description:';
            jobInput.placeholder = 'Paste the complete job description text here...';
        }
        
        jobInput.value = '';
        errorMessage.classList.add('hidden');
    });
});

// Form submission
analyzeForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    const jobInputValue = jobInput.value.trim();

    // Validate input
    if (!jobInputValue) {
        showError('Please provide job URL or description');
        return;
    }

    // Basic validation for URL mode
    if (currentInputType === 'url' && !isValidUrl(jobInputValue)) {
        showError('Please enter a valid URL');
        return;
    }

    // Basic validation for text mode
    if (currentInputType === 'text' && jobInputValue.length < 50) {
        showError('Job description is too short. Please provide more details.');
        return;
    }

    // Show loading state
    showLoading();
    errorMessage.classList.add('hidden');

    try {
        // Call API
        const result = await analyzeJob(jobInputValue, currentInputType);

        // Store result and redirect
        sessionStorage.setItem('analysisResult', JSON.stringify(result));
        window.location.href = '/result';

    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'An error occurred during analysis');
        hideLoading();
    }
});

// ==================== API FUNCTIONS ====================

/**
 * Analyze job posting via API
 */
async function analyzeJob(jobInput, inputType) {
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                job_input: jobInput,
                input_type: inputType
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Analysis failed');
        }

        if (!data.success && data.error) {
            throw new Error(data.error);
        }

        return data;

    } catch (error) {
        throw new Error(error.message || 'Failed to analyze job');
    }
}

/**
 * Get supported portals
 */
async function getSupportedPortals() {
    try {
        const response = await fetch('/api/supported-portals');
        const data = await response.json();
        return data.supported_portals;
    } catch (error) {
        console.error('Error fetching portals:', error);
        return [];
    }
}

/**
 * Test analysis endpoint
 */
async function testAnalysis() {
    try {
        const response = await fetch('/api/test-analysis');
        const data = await response.json();
        console.log('Test result:', data);
        return data;
    } catch (error) {
        console.error('Error in test analysis:', error);
    }
}

// ==================== UI FUNCTIONS ====================

/**
 * Show loading state
 */
function showLoading() {
    loadingState.classList.remove('hidden');
    analyzeBtn.disabled = true;
}

/**
 * Hide loading state
 */
function hideLoading() {
    loadingState.classList.add('hidden');
    analyzeBtn.disabled = false;
}

/**
 * Show error message
 */
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Scroll to analyzer section
 */
function scrollToAnalyzer() {
    const analyzer = document.getElementById('analyzer');
    if (analyzer) {
        analyzer.scrollIntoView({ behavior: 'smooth' });
    }
}

// ==================== VALIDATION FUNCTIONS ====================

/**
 * Validate URL format
 */
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

/**
 * Check if URL is from supported portal
 */
function isSupportedPortal(url) {
    const supportedDomains = [
        'linkedin.com',
        'naukri.com',
        'indeed.com',
        'internshala.com',
        'monster.com',
        'glassdoor.com'
    ];
    
    return supportedDomains.some(domain => url.toLowerCase().includes(domain));
}

// ==================== INITIALIZATION ====================

/**
 * Initialize page
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Page loaded successfully');
    
    // Set first toggle as active
    if (toggleBtns.length > 0) {
        toggleBtns[0].classList.add('active');
    }
});

// ==================== UTILITY FUNCTIONS ====================

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('Copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

/**
 * Format date
 */
function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Truncate text
 */
function truncateText(text, maxLength = 100) {
    if (text.length <= maxLength) {
        return text;
    }
    return text.substring(0, maxLength) + '...';
}

/**
 * Highlight text
 */
function highlightText(text, keywords) {
    let highlightedText = text;
    keywords.forEach(keyword => {
        const regex = new RegExp(`(${keyword})`, 'gi');
        highlightedText = highlightedText.replace(regex, '<mark>$1</mark>');
    });
    return highlightedText;
}

// ==================== EXPORT FUNCTIONS ====================
window.scrollToAnalyzer = scrollToAnalyzer;
window.analyzeJob = analyzeJob;
window.getSupportedPortals = getSupportedPortals;
window.testAnalysis = testAnalysis;
