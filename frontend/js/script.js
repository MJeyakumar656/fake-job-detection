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
    btn.addEventListener('click', function () {
        toggleBtns.forEach(b => b.classList.remove('active'));
        this.classList.add('active');

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
analyzeForm.addEventListener('submit', async function (e) {
    e.preventDefault();

    const jobInputValue = jobInput.value.trim();

    if (!jobInputValue) {
        showError('Please provide job URL or description');
        return;
    }

    if (currentInputType === 'url' && !isValidUrl(jobInputValue)) {
        showError('Please enter a valid URL');
        return;
    }

    if (currentInputType === 'text' && jobInputValue.length < 50) {
        showError('Job description is too short. Please provide more details.');
        return;
    }

    showLoading();
    errorMessage.classList.add('hidden');

    try {
        const result = await analyzeJob(jobInputValue, currentInputType);
        sessionStorage.setItem('analysisResult', JSON.stringify(result));
        window.location.href = 'result.html';
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'An error occurred during analysis');
        hideLoading();
    }
});

// ==================== API FUNCTIONS ====================

async function analyzeJob(jobInputVal, inputType) {
    try {
        const response = await apiRequest('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                job_input: jobInputVal,
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

// ==================== UI FUNCTIONS ====================

function showLoading() {
    loadingState.classList.remove('hidden');
    analyzeBtn.disabled = true;
}

function hideLoading() {
    loadingState.classList.add('hidden');
    analyzeBtn.disabled = false;
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function scrollToAnalyzer() {
    const analyzer = document.getElementById('analyzer');
    if (analyzer) {
        analyzer.scrollIntoView({ behavior: 'smooth' });
    }
}

// ==================== VALIDATION ====================

function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', function () {
    console.log('✅ Page loaded successfully');
    if (toggleBtns.length > 0) {
        toggleBtns[0].classList.add('active');
    }

    // Mobile menu toggle
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    if (hamburger) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
    }
});

window.scrollToAnalyzer = scrollToAnalyzer;
window.analyzeJob = analyzeJob;
