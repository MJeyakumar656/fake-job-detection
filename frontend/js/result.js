// ==================== DOM ELEMENTS ====================
const predictionBadge = document.getElementById('predictionBadge');
const predictionText = document.getElementById('predictionText');
const predictionDescription = document.getElementById('predictionDescription');
const jobPortal = document.getElementById('jobPortal');
const companyName = document.getElementById('companyName');
const companyDomain = document.getElementById('companyDomain');
const jobTitle = document.getElementById('jobTitle');
const jobLocation = document.getElementById('jobLocation');
const qualityBadge = document.getElementById('qualityBadge');
const confidencePercentage = document.getElementById('confidencePercentage');
const confidenceFill = document.getElementById('confidenceFill');
const redFlagCount = document.getElementById('redFlagCount');
const redFlagsList = document.getElementById('redFlagsList');
const severityLevel = document.getElementById('severityLevel');
const descriptionPreview = document.getElementById('descriptionPreview');
const recommendationList = document.getElementById('recommendationList');

// ==================== INITIALIZATION ====================

/**
 * Initialize result page
 */
document.addEventListener('DOMContentLoaded', function () {
    console.log('Result page loaded');

    // Get analysis result from session storage or session
    const result = getAnalysisResult();

    if (result) {
        displayResult(result);
    } else {
        console.error('No analysis result found');
        redirectToHome();
    }
});

// ==================== DATA RETRIEVAL ====================

/**
 * Get analysis result from storage
 */
function getAnalysisResult() {
    // Try sessionStorage first
    let result = sessionStorage.getItem('analysisResult');
    if (result) {
        return JSON.parse(result);
    }

    // Try window data (passed from server)
    if (window.analysisResult) {
        return window.analysisResult;
    }

    return null;
}

// ==================== DISPLAY FUNCTIONS ====================

/**
 * Display analysis result
 */
function displayResult(result) {
    console.log('Displaying result:', result);

    if (!result || result.error) {
        showErrorState(result?.error || 'No result available');
        return;
    }

    try {
        // Display prediction badge
        displayPredictionBadge(result);

        // Display job details
        displayJobDetails(result);

        // Display confidence score
        displayConfidenceScore(result);

        // Display red flags
        displayRedFlags(result);

        // Display description preview
        displayDescription(result);

        // Display recommendations
        displayRecommendations(result);

        console.log('Result displayed successfully');
    } catch (error) {
        console.error('Error displaying result:', error);
        showErrorState('Error displaying result');
    }
}

/**
 * Display prediction badge
 */
function displayPredictionBadge(result) {
    const isFake = result.is_fake;
    const confidence = result.combined_confidence || result.ai_confidence || 0;

    // Update badge styling
    if (isFake) {
        predictionBadge.style.background = 'linear-gradient(135deg, #ff6b6b 0%, #ff4757 100%)';
        predictionText.textContent = 'FAKE JOB';
        predictionDescription.textContent = 'This job posting shows strong signs of being fraudulent';
    } else {
        predictionBadge.style.background = 'linear-gradient(135deg, #51cf66 0%, #40c057 100%)';
        predictionText.textContent = 'GENUINE JOB';

        // Provide description based on confidence level
        if (confidence > 70) {
            predictionDescription.textContent = 'This job posting shows minimal red flags and appears trustworthy';
        } else if (confidence > 40) {
            predictionDescription.textContent = 'This job posting shows some positive indicators, but verify independently';
        } else {
            predictionDescription.textContent = 'This job posting requires additional verification';
        }
    }
}

/**
 * Display job details
 */
function displayJobDetails(result) {
    jobPortal.textContent = result.job_portal || 'Unknown';
    companyName.textContent = result.company || 'Unknown';
    companyDomain.textContent = result.company_domain || 'N/A';
    jobTitle.textContent = result.job_title || 'Unknown';
    jobLocation.textContent = result.location || 'Not Specified';

    // Display quality badge
    const quality = result.job_quality || 'Low';
    qualityBadge.textContent = quality;
    qualityBadge.className = 'quality-badge';
}

/**
 * Display confidence score
 */
function displayConfidenceScore(result) {
    const confidence = result.combined_confidence || result.ai_confidence || 50;

    confidencePercentage.textContent = confidence.toFixed(1) + '%';
    confidenceFill.style.width = confidence + '%';

    // Update color based on confidence
    if (confidence > 70) {
        confidenceFill.style.background = 'linear-gradient(90deg, #ff6b6b, #ff4757)';
    } else if (confidence > 50) {
        confidenceFill.style.background = 'linear-gradient(90deg, #ffd93d, #ff9800)';
    } else {
        confidenceFill.style.background = 'linear-gradient(90deg, #51cf66, #40c057)';
    }
}

/**
 * Display red flags
 */
function displayRedFlags(result) {
    const redFlags = result.red_flags_list || [];
    const count = result.red_flags_count || 0;

    redFlagCount.textContent = count;
    severityLevel.textContent = result.red_flags_severity || 'Low';

    // Clear existing red flags
    redFlagsList.innerHTML = '';

    if (count === 0) {
        redFlagsList.innerHTML = '<div style="text-align: center; color: var(--success-color);"><i class="fas fa-check-circle"></i> No red flags detected</div>';
        return;
    }

    // Display red flags
    redFlags.forEach(flag => {
        const flagItem = document.createElement('div');
        flagItem.className = 'red-flag-item';

        const description = flag.replace(/_/g, ' ');

        flagItem.innerHTML = '<i class="fas fa-times-circle"></i><span>' + description + '</span>';

        redFlagsList.appendChild(flagItem);
    });
}

/**
 * Display job description preview
 */
function displayDescription(result) {
    const description = result.description_preview || result.description || '';
    const descriptionSection = document.querySelector('.description-section');

    if (description && description.trim() !== '') {
        const maxLength = 1000;
        let displayText = description;

        if (displayText.length > maxLength) {
            displayText = displayText.substring(0, maxLength) + '...';
        }

        descriptionPreview.textContent = displayText;
        descriptionSection.style.display = 'block';
    } else {
        const jobDetails = 'Job Title: ' + (result.job_title || 'Not specified') +
            '\nCompany: ' + (result.company || 'Not specified') +
            '\nLocation: ' + (result.location || 'Not specified') +
            '\nPortal: ' + (result.job_portal || 'Not specified');

        descriptionPreview.textContent = jobDetails;
        descriptionSection.style.display = 'block';
    }
}

/**
 * Display recommendations
 */
function displayRecommendations(result) {
    const isFake = result.is_fake;
    const redFlags = result.red_flags_list || [];
    const confidence = result.combined_confidence || result.ai_confidence || 0;

    let recommendations = [];

    if (isFake) {
        recommendations.push('Do NOT apply to this job posting. It shows clear signs of being fraudulent.');
        recommendations.push('Report this job posting to the job portal immediately.');
        recommendations.push('Search for similar positions from reputable companies instead.');
    } else {
        // Recommendations based on confidence
        if (confidence > 70) {
            recommendations.push('This job posting has low risk indicators. However, always verify through official channels.');
            recommendations.push('Contact the company directly using official email addresses.');
        } else if (confidence > 40) {
            recommendations.push('This job posting shows some positive signs but has moderate confidence.');
            recommendations.push('Conduct additional research on the company before applying.');
            recommendations.push('Verify the job posting on the company website.');
        } else {
            recommendations.push('Exercise caution and thoroughly verify all details before applying.');
            recommendations.push('Contact the company through official channels only.');
            recommendations.push('Research the company thoroughly.');
        }
    }

    // Add specific recommendations based on red flags
    if (redFlags.includes('unrealistic_salary')) {
        recommendations.push('The salary mentioned seems unrealistic. Verify with industry standards.');
    }

    if (redFlags.includes('suspicious_email') || redFlags.includes('has_suspicious_domain')) {
        recommendations.push('The company email or domain looks suspicious. Verify through official company website.');
    }

    // Display recommendations
    recommendationList.innerHTML = '';

    recommendations.forEach(rec => {
        const recItem = document.createElement('div');
        recItem.className = 'recommendation-item';
        recItem.innerHTML = '<p>' + rec + '</p>';
        recommendationList.appendChild(recItem);
    });
}

/**
 * Show error state
 */
function showErrorState(error) {
    const container = document.querySelector('.result-container');
    container.innerHTML = '<div class="alert alert-error" style="display: block;"><i class="fas fa-exclamation-circle"></i><strong>Error:</strong> ' + error + '</div><button class="btn btn-primary btn-large" onclick="location.href=\'/\'"><i class="fas fa-home"></i> Go Back Home</button>';
}

// ==================== ACTION FUNCTIONS ====================

/**
 * Download report
 */
async function downloadReport() {
    const result = getAnalysisResult();

    if (!result) {
        alert('No analysis result to download');
        return;
    }

    const reportContent = 'FAKE JOB DETECTION ANALYSIS REPORT\n==================================\n\nGenerated: ' + new Date().toLocaleString() + '\n\nPREDICTION\n----------\nStatus: ' + (result.is_fake ? 'FAKE JOB' : 'GENUINE JOB') + '\nConfidence: ' + (result.combined_confidence || result.ai_confidence).toFixed(1) + '%\nQuality: ' + (result.job_quality || 'Unknown') + '\n\nJOB DETAILS\n-----------\nPortal: ' + result.job_portal + '\nCompany: ' + result.company + '\nDomain: ' + result.company_domain + '\nTitle: ' + result.job_title + '\nLocation: ' + result.location + '\n\nRED FLAGS: ' + result.red_flags_count + '\n-----------\n' + (result.red_flags_list ? result.red_flags_list.join('\n') : 'None') + '\n\n==================================\nThis report was generated by JobGuard AI';

    const blob = new Blob([reportContent], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'job-analysis-report-' + Date.now() + '.txt';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

/**
 * Share result
 */
async function shareResult() {
    const result = getAnalysisResult();

    if (!result) {
        alert('No analysis result to share');
        return;
    }

    const shareText = 'JobGuard AI - Job Analysis\n\nJob: ' + result.job_title + '\nCompany: ' + result.company + '\nStatus: ' + (result.is_fake ? 'FAKE JOB' : 'GENUINE JOB') + '\nConfidence: ' + (result.combined_confidence || result.ai_confidence).toFixed(1) + '%\nRed Flags: ' + result.red_flags_count;

    if (navigator.share) {
        try {
            await navigator.share({
                title: 'JobGuard AI - Job Analysis',
                text: shareText,
                url: window.location.href
            });
        } catch (error) {
            console.log('Share cancelled or failed:', error);
        }
    } else {
        navigator.clipboard.writeText(shareText).then(() => {
            alert('Analysis result copied to clipboard!');
        });
    }
}

/**
 * Redirect to home
 */
function redirectToHome() {
    window.location.href = 'index.html';
}

// ==================== EXPORT FUNCTIONS ====================
window.downloadReport = downloadReport;
window.shareResult = shareResult;
window.redirectToHome = redirectToHome;
