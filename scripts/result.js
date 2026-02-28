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
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Result page loaded');
    
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

        console.log('✅ Result displayed successfully');
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
        predictionDescription.textContent = `This job posting shows strong signs of being fraudulent (${confidence.toFixed(1)}% confidence)`;
    } else {
        predictionBadge.style.background = 'linear-gradient(135deg, #51cf66 0%, #40c057 100%)';
        predictionText.textContent = 'GENUINE JOB';
        predictionDescription.textContent = `This job posting appears to be legitimate (${confidence.toFixed(1)}% confidence)`;
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
    
    // Display quality badge with enhanced levels
    const quality = result.job_quality || 'Low';
    qualityBadge.textContent = quality;
    qualityBadge.className = 'quality-badge';

    // Map quality levels to CSS classes
    const qualityClassMap = {
        'EXCELLENT': 'excellent-quality',
        'VERY HIGH': 'very-high-quality',
        'HIGH': 'high-quality',
        'GOOD': 'good-quality',
        'MODERATE': 'moderate-quality',
        'FAIR': 'fair-quality',
        'LOW': 'low-quality',
        'VERY LOW': 'very-low-quality',
        'POOR': 'poor-quality',
        'SUSPICIOUS': 'suspicious-quality'
    };

    // Add the appropriate quality class
    const qualityClass = qualityClassMap[quality] || 'low-quality';
    qualityBadge.classList.add(qualityClass);
}

/**
 * Display confidence score
 */
function displayConfidenceScore(result) {
    const confidence = result.combined_confidence || result.ai_confidence || 50;
    
    confidencePercentage.textContent = `${confidence.toFixed(1)}%`;
    confidenceFill.style.width = `${confidence}%`;
    
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
    
    // Display red flags - comprehensive list covering all detection patterns
    const flagDescriptions = {
        // Original flags
        'unrealistic_salary': 'Unrealistic salary promise',
        'vague_description': 'Vague job description',
        'spam_phrase': 'Contains spam phrases (get rich quick, work from home, etc.)',
        'poor_formatting': 'Poor text formatting',
        'missing_requirements': 'Missing job requirements',
        'suspicious_email': 'Suspicious email address',
        'has_suspicious_domain': 'Suspicious company domain',
        'spelling_errors': 'Multiple spelling errors',
        'generic_description': 'Generic job description',
        'short_description': 'Very short job description',
        'excessive_errors': 'Excessive grammar/spelling errors',
        'fake_domain': 'Fake or temporary domain',
        'contact_details_missing': 'Missing proper contact details',
        'cryptocurrency_mention': 'Cryptocurrency or Bitcoin mentioned',

        // Enhanced detection flags
        'registration fee': 'Requires registration or application fee',
        'pay fee': 'Requires payment to apply or start',
        'payment required': 'Payment required upfront',
        'upfront payment': 'Upfront payment demanded',
        'processing fee': 'Processing fee required',
        'application fee': 'Application fee charged',
        'training fee': 'Training fee required',
        'deposit required': 'Security deposit required',
        'money transfer': 'Money transfer requested',
        'western union': 'Western Union payment mentioned',
        'wire transfer': 'Wire transfer requested',
        'bitcoin': 'Bitcoin or cryptocurrency mentioned',
        'cryptocurrency': 'Cryptocurrency investment required',
        'blockchain investment': 'Blockchain investment scheme',
        'crypto investment': 'Crypto investment required',
        'guaranteed income': 'Guaranteed income promised',
        'guaranteed job': 'Job guarantee claimed',
        'earn $': 'Unrealistic earnings promise',
        'earn ₹': 'Unrealistic earnings in rupees',
        'make money fast': 'Make money fast promise',
        'easy money': 'Easy money claim',
        'get rich quick': 'Get rich quick scheme',
        'no interview': 'No interview required',
        'no interview process': 'No interview process',
        'no assessment': 'No assessment required',
        'skip interview': 'Interview can be skipped',
        'instant hire': 'Instant hiring promised',
        'instant approval': 'Instant approval claimed',
        'no verification': 'No verification required',
        'no background check': 'No background check',
        'no experience needed': 'No experience required',
        'no qualification needed': 'No qualifications required',
        'no degree required': 'No degree required',
        'fake degree accepted': 'Fake degrees accepted',
        'forged documents': 'Forged documents accepted',
        'illegal work': 'Illegal work mentioned',
        'underground job': 'Underground job',
        'black market': 'Black market reference',

        // Work pattern flags
        'work from home guaranteed': 'Guaranteed work from home',
        'urgent hiring': 'Urgent hiring claim',
        'urgent recruitment': 'Urgent recruitment',
        'limited time offer': 'Limited time offer',
        'limited positions': 'Limited positions available',
        'act now': 'Act now pressure',
        'don\'t miss': 'Don\'t miss opportunity',
        'don\'t delay': 'Don\'t delay warning',
        'hurry up': 'Hurry up pressure',
        'apply immediately': 'Apply immediately',
        'apply asap': 'Apply ASAP',
        'freshers welcome': 'Freshers welcome (suspicious)',
        'guaranteed placement': 'Guaranteed placement',
        '100% job guarantee': '100% job guarantee',
        'click here': 'Click here instruction',
        'click link': 'Click link instruction',
        'copy paste': 'Copy-paste work',
        'copy-paste': 'Copy-paste job',
        'home based': 'Home-based work',
        'part time': 'Part-time work (suspicious context)',
        'passive income': 'Passive income promise',
        'side hustle': 'Side hustle opportunity',
        'extra income': 'Extra income claim',
        'earn while you': 'Earn while you...',
        'earn from home': 'Earn from home',

        // Contact method flags
        'whatsapp': 'WhatsApp contact required',
        'telegram': 'Telegram contact required',
        'viber': 'Viber contact required',
        'skype': 'Skype contact required',
        'contact via whatsapp': 'Contact via WhatsApp',
        'contact via telegram': 'Contact via Telegram',
        'dm only': 'DM only contact',
        'dm for details': 'DM for details',
        'message for details': 'Message for details',
        'inbox for details': 'Inbox for details',
        'only whatsapp': 'WhatsApp only',
        'strictly whatsapp': 'Strictly WhatsApp',
        'exclusively whatsapp': 'Exclusively WhatsApp',

        // MLM and pyramid flags
        'mlm': 'MLM mentioned',
        'multi level marketing': 'Multi-level marketing',
        'pyramid': 'Pyramid scheme',
        'network marketing': 'Network marketing',
        'referral bonus': 'Referral bonus offered',
        'referral commission': 'Referral commission',
        'recruitment bonus': 'Recruitment bonus',
        'refer friends': 'Refer friends',
        'refer and earn': 'Refer and earn',
        'get commission': 'Commission offered',
        'commission only': 'Commission only',
        'no salary': 'No salary mentioned',
        'performance based': 'Performance based pay',
        'variable pay': 'Variable pay only',
        'bonus heavy': 'Bonus heavy compensation',

        // Scam-specific phrases
        'get rich quick': 'Get rich quick scheme',
        'easy money': 'Easy money promise',
        'passive income': 'Passive income',
        'residual income': 'Residual income',
        'work from home': 'Work from home (suspicious context)',
        'remote work': 'Remote work (guaranteed)',
        'no experience': 'No experience needed',
        'no skills': 'No skills required',
        'no qualification': 'No qualification needed',

        // AI/ML scam flags
        'ai job': 'AI job (suspicious context)',
        'artificial intelligence job': 'AI job opportunity',
        'machine learning job': 'ML job opportunity',
        'ml job': 'ML job opportunity',
        'deep learning job': 'Deep learning job',
        'ai certification': 'AI certification (paid)',
        'ml certification': 'ML certification (paid)',
        'data science certification': 'Data science certification',
        'ai training': 'AI training (investment required)',
        'ml training': 'ML training (investment required)',

        // Crypto/blockchain flags
        'blockchain developer': 'Blockchain developer job',
        'crypto developer': 'Crypto developer job',
        'web3 developer': 'Web3 developer job',
        'nft developer': 'NFT developer job',
        'metaverse job': 'Metaverse job',
        'vr job': 'VR job',
        'ar job': 'AR job',
        'virtual reality job': 'Virtual reality job',

        // Modern remote work scams
        'remote unlimited': 'Unlimited remote work',
        'unrestricted remote': 'Unrestricted remote work',
        'freedom remote': 'Remote work freedom',
        'set your own hours': 'Set your own hours',
        'work when you want': 'Work when you want',
        'own boss': 'Be your own boss',
        'no boss': 'No boss',
        'no manager': 'No manager',
        'no supervisor': 'No supervisor',
        'no office': 'No office required',

        // Unrealistic promises
        'learn coding in 2 weeks': 'Impossible coding timeline',
        'learn programming in 2 weeks': 'Impossible programming timeline',
        'become developer in 1 month': 'Unrealistic developer timeline',
        'become engineer in 1 month': 'Unrealistic engineer timeline',
        'guaranteed placement': 'Guaranteed placement promise',
        'job after course': 'Job guarantee after course',

        // Advanced scam tactics
        'copy paste work': 'Copy-paste work',
        'micro tasks': 'Micro tasks',
        'nano tasks': 'Nano tasks',
        'click work': 'Click work',
        'captcha entry': 'Captcha entry work',
        'crowdfunding': 'Crowdfunding platform',
        'crowdsource': 'Crowdsourcing platform',
        'upwork alternative': 'Upwork alternative',
        'fiverr competitor': 'Fiverr competitor',

        // Investment scams
        'invest small amount': 'Small investment required',
        'initial investment': 'Initial investment needed',
        'roi': 'ROI promised',
        'return on investment': 'Return on investment',
        'profit sharing': 'Profit sharing',
        'revenue sharing': 'Revenue sharing',
        'partnership': 'Business partnership',
        'joint venture': 'Joint venture',
        'business opportunity': 'Business opportunity',

        // Psychological manipulation
        'limited spots': 'Limited spots available',
        'exclusive opportunity': 'Exclusive opportunity',
        'vip access': 'VIP access',
        'don\'t tell anyone': 'Secrecy required',
        'keep it confidential': 'Keep confidential',
        'only serious candidates': 'Only serious candidates',
        'serious applicants only': 'Serious applicants only',

        // Fake company indicators
        'startup unlimited potential': 'Startup with unlimited potential',
        'emerging company': 'Emerging company (suspicious)',
        'high growth startup': 'High growth startup',
        'revolutionary technology': 'Revolutionary technology',
        'disruptive technology': 'Disruptive technology',
        'game changing platform': 'Game-changing platform',
        'backed by celebrity': 'Celebrity backed',
        'funded by influencer': 'Influencer funded',

        // Quality indicators (negative when present)
        'poor sentence structure': 'Poor sentence structure',
        'missing professional job details': 'Missing professional details',
        'limited professional content': 'Limited professional content',
        'high scam phrase density': 'High scam phrase density',
        'multiple contact methods': 'Multiple contact methods',
        'excessive money references': 'Excessive money references',
        'high urgency pressure': 'High urgency pressure',
        'all caps text': 'ALL CAPS TEXT',
        'excessive capitalization': 'Excessive capitalization'
    };
    
    redFlags.forEach(flag => {
        const flagItem = document.createElement('div');
        flagItem.className = 'red-flag-item';
        
        const description = flagDescriptions[flag] || flag.replace(/_/g, ' ');
        
        flagItem.innerHTML = `
            <i class="fas fa-times-circle"></i>
            <span>${description}</span>
        `;
        
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
        // Show description if available
        const maxLength = 1000;
        let displayText = description;

        if (displayText.length > maxLength) {
            displayText = displayText.substring(0, maxLength) + '...';
        }

        descriptionPreview.textContent = displayText;
        descriptionSection.style.display = 'block';
    } else {
        // Show job details if no description
        const jobDetails = `
            Job Title: ${result.job_title || 'Not specified'}
            Company: ${result.company || 'Not specified'}
            Location: ${result.location || 'Not specified'}
            Portal: ${result.job_portal || 'Not specified'}
            Job Type: ${result.job_type || 'Not specified'}
            Experience Level: ${result.experience_level || 'Not specified'}
        `.trim();

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
    
    let recommendations = [];
    
    if (isFake) {
        recommendations.push('⚠️ <strong>Do NOT apply</strong> to this job posting. It shows clear signs of being fraudulent.');
        recommendations.push('🔍 Report this job posting to the job portal immediately.');
        recommendations.push('💼 Search for similar positions from reputable companies instead.');
    } else {
        recommendations.push('✅ This job appears to be legitimate. You can proceed with caution.');
        recommendations.push('📧 Contact the company through official channels to verify the job posting.');
        recommendations.push('💬 Ask for official company email and do additional research about the company.');
    }
    
    // Add specific recommendations based on red flags
    if (redFlags.includes('unrealistic_salary')) {
        recommendations.push('⚠️ The salary mentioned seems unrealistic. Verify with industry standards.');
    }
    
    if (redFlags.includes('suspicious_email') || redFlags.includes('has_suspicious_domain')) {
        recommendations.push('⚠️ The company email or domain looks suspicious. Verify through official company website.');
    }
    
    if (redFlags.includes('missing_requirements')) {
        recommendations.push('⚠️ The job posting lacks proper requirements. Request more details before applying.');
    }
    
    if (redFlags.includes('spelling_errors')) {
        recommendations.push('⚠️ Multiple spelling errors suggest low professionalism. Be cautious.');
    }
    
    // Display recommendations
    recommendationList.innerHTML = '';
    
    recommendations.forEach(rec => {
        const recItem = document.createElement('div');
        recItem.className = 'recommendation-item';
        recItem.innerHTML = `<p>${rec}</p>`;
        recommendationList.appendChild(recItem);
    });
}

/**
 * Show error state
 */
function showErrorState(error) {
    const container = document.querySelector('.result-container');
    container.innerHTML = `
        <div class="alert alert-error" style="display: block;">
            <i class="fas fa-exclamation-circle"></i>
            <strong>Error:</strong> ${error}
        </div>
        <button class="btn btn-primary btn-large" onclick="location.href='/'">
            <i class="fas fa-home"></i> Go Back Home
        </button>
    `;
}

// ==================== ACTION FUNCTIONS ====================

/**
 * Download report as PDF/Text
 */
async function downloadReport() {
    const result = getAnalysisResult();
    
    if (!result) {
        alert('No analysis result to download');
        return;
    }
    
    // Create report content
    let reportContent = `
FAKE JOB DETECTION ANALYSIS REPORT
==================================

Generated: ${new Date().toLocaleString()}

PREDICTION
----------
Status: ${result.is_fake ? 'FAKE JOB' : 'GENUINE JOB'}
Confidence: ${(result.combined_confidence || result.ai_confidence).toFixed(1)}%
Quality: ${result.job_quality || 'Unknown'}

JOB DETAILS
-----------
Portal: ${result.job_portal}
Company: ${result.company}
Domain: ${result.company_domain}
Title: ${result.job_title}
Location: ${result.location}

RED FLAGS (${result.red_flags_count})
-----------
${result.red_flags_list?.map((flag, i) => `${i + 1}. ${flag}`).join('\n') || 'None'}

DESCRIPTION PREVIEW
-------------------
${result.description_preview || 'N/A'}

RECOMMENDATIONS
---------------
${Array.from(document.querySelectorAll('.recommendation-item p'))
    .map(p => '- ' + p.textContent)
    .join('\n')}

==================================
This report was generated by JobGuard AI - Fake Job Detection System
Visit: https://jobguard-ai.com
    `;
    
    // Create blob and download
    const blob = new Blob([reportContent], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `job-analysis-report-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    console.log('✅ Report downloaded');
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
    
    const shareText = `
🔍 JobGuard AI - Fake Job Detection Result

Job: ${result.job_title}
Company: ${result.company}
Status: ${result.is_fake ? '⚠️ FAKE JOB' : '✅ GENUINE JOB'}
Confidence: ${(result.combined_confidence || result.ai_confidence).toFixed(1)}%
Red Flags: ${result.red_flags_count}

Check suspicious job postings with AI-powered detection!
    `;
    
    // Use Web Share API if available
    if (navigator.share) {
        try {
            await navigator.share({
                title: 'JobGuard AI - Job Analysis',
                text: shareText,
                url: window.location.href
            });
            console.log('✅ Result shared successfully');
        } catch (error) {
            console.log('Share cancelled or failed:', error);
        }
    } else {
        // Fallback: Copy to clipboard
        navigator.clipboard.writeText(shareText).then(() => {
            alert('Analysis result copied to clipboard!');
        });
    }
}

/**
 * Redirect to home
 */
function redirectToHome() {
    window.location.href = '/';
}

// ==================== EXPORT FUNCTIONS ====================
window.downloadReport = downloadReport;
window.shareResult = shareResult;
window.redirectToHome = redirectToHome;
