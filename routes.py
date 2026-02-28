from flask import Blueprint, request, jsonify, session
from src.analyzer import JobAnalyzer
import logging
from functools import wraps

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize analyzer (lazy loading)
_analyzer = None

def get_analyzer():
    """Get or create analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = JobAnalyzer()
    return _analyzer

def detect_input_type(job_input):
    """Auto-detect if input is URL or text"""
    job_input = job_input.strip()

    # Check if it looks like a URL
    if (job_input.startswith(('http://', 'https://', 'www.')) or
        '://' in job_input or
        any(domain in job_input.lower() for domain in [
            'linkedin.com', 'naukri.com', 'indeed.com', 'internshala.com',
            'jobs.', '.com/jobs', '/job'
        ])):
        return 'url'

    # Check if it looks like job description text
    if (len(job_input) > 100 and
        any(keyword in job_input.lower() for keyword in [
            'responsibilities', 'requirements', 'qualifications', 'skills',
            'experience', 'salary', 'company', 'location', 'benefits'
        ])):
        return 'text'

    # Default to URL if it contains common URL patterns
    if ('/' in job_input and len(job_input.split('/')) > 3) or '@' in job_input:
        return 'url'

    # Default to text for shorter inputs or unclear cases
    return 'text'

def validate_job_input(job_input, input_type):
    """Enhanced validation for job input based on type"""
    result = {'valid': True, 'portal': None, 'warnings': []}

    if input_type == 'url':
        # URL validation
        if not job_input.startswith(('http://', 'https://')):
            if job_input.startswith('www.'):
                job_input = 'https://' + job_input
            else:
                result['valid'] = False
                result['error'] = 'URL must start with http:// or https://'
                return result

        # Check if URL is accessible
        try:
            from urllib.parse import urlparse
            parsed = urlparse(job_input)
            if not parsed.netloc:
                result['valid'] = False
                result['error'] = 'Invalid URL format'
                return result
        except:
            result['valid'] = False
            result['error'] = 'Invalid URL format'
            return result

        # Detect job portal
        job_input_lower = job_input.lower()
        portals = {
            'linkedin': 'linkedin.com',
            'naukri': 'naukri.com',
            'indeed': 'indeed.com',
            'internshala': 'internshala.com'
        }

        for portal_name, domain in portals.items():
            if domain in job_input_lower:
                result['portal'] = portal_name
                break

        if not result['portal']:
            result['warnings'].append('URL is not from a supported job portal. Analysis may be limited.')

        # Check for suspicious URL patterns
        suspicious_patterns = ['bit.ly', 'tinyurl', 'goo.gl', 'temp-mail', '10minutemail']
        if any(pattern in job_input_lower for pattern in suspicious_patterns):
            result['warnings'].append('URL contains link shortener or temporary service - this is suspicious')

    else:  # text input
        # Text validation
        if len(job_input) < 50:
            result['valid'] = False
            result['error'] = 'Job description is too short. Please provide more details.'
            return result

        if len(job_input) > 10000:
            result['warnings'].append('Job description is very long. Analysis may take longer.')

        # Check for minimum professional content
        professional_keywords = [
            'responsibilities', 'requirements', 'qualifications', 'skills',
            'experience', 'education', 'benefits', 'salary', 'compensation'
        ]

        found_keywords = sum(1 for keyword in professional_keywords if keyword in job_input.lower())
        if found_keywords < 2:
            result['warnings'].append('Job description lacks standard professional sections. This may indicate a suspicious posting.')

        # Check for excessive special characters
        special_chars = sum(1 for char in job_input if not char.isalnum() and char not in ' .,!?-()')
        special_ratio = special_chars / len(job_input) if job_input else 0
        if special_ratio > 0.1:
            result['warnings'].append('Job description contains many special characters - this is unusual')

    return result

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    analyzer = get_analyzer()
    return jsonify({
        'status': 'healthy',
        'message': 'Fake Job Detection API is running',
        'model_loaded': analyzer.model_loaded
    }), 200

@api_bp.route('/analyze', methods=['POST'])
def analyze_job():
    """Main endpoint to analyze job posting with enhanced validation"""
    try:
        data = request.json
        analyzer = get_analyzer()

        # Validate input
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        job_input = data.get('job_input', '').strip()
        input_type = data.get('input_type', 'auto').strip()

        if not job_input:
            return jsonify({'error': 'Please provide job URL or description'}), 400

        # Auto-detect input type if not specified or set to 'auto'
        if input_type == 'auto':
            input_type = detect_input_type(job_input)

        if input_type not in ['url', 'text']:
            return jsonify({'error': 'Invalid input_type. Use "url", "text", or "auto"'}), 400

        # Enhanced validation based on input type
        validation_result = validate_job_input(job_input, input_type)
        if not validation_result['valid']:
            return jsonify({'error': validation_result['error']}), 400

        logger.info(f"Analyzing job - Type: {input_type}, Length: {len(job_input)}, Portal: {validation_result.get('portal', 'N/A')}")

        # Analyze based on input type
        if input_type == 'url':
            result = analyzer.analyze_from_url(job_input)
        else:
            result = analyzer.analyze_from_text(job_input)

        # Check if analysis was successful
        if not result.get('success', True) and result.get('error'):
            return jsonify(result), 400

        # Add validation info to result
        result['input_validation'] = validation_result

        # Store result in session for result page
        session['last_analysis'] = result

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error analyzing job: {str(e)}", exc_info=True)
        return jsonify({
            'error': f'Server error: {str(e)}',
            'success': False
        }), 500

@api_bp.route('/analyze-batch', methods=['POST'])
def analyze_batch():
    """Analyze multiple job postings"""
    try:
        data = request.json
        analyzer = get_analyzer()
        
        if not data or 'jobs' not in data:
            return jsonify({'error': 'Please provide jobs list'}), 400
        
        jobs = data.get('jobs', [])
        
        if not isinstance(jobs, list) or len(jobs) == 0:
            return jsonify({'error': 'jobs must be a non-empty list'}), 400
        
        results = []
        
        for idx, job in enumerate(jobs, 1):
            job_input = job.get('job_input', '').strip()
            input_type = job.get('input_type', 'url').strip()
            
            if not job_input:
                results.append({'error': 'Empty job input', 'success': False})
                continue
            
            logger.info(f"Batch analyzing job {idx}/{len(jobs)}")
            
            if input_type == 'url':
                result = analyzer.analyze_from_url(job_input)
            else:
                result = analyzer.analyze_from_text(job_input)
            
            results.append(result)
        
        return jsonify({
            'total_jobs': len(jobs),
            'results': results,
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Batch analysis error: {str(e)}", exc_info=True)
        return jsonify({
            'error': f'Server error: {str(e)}',
            'success': False
        }), 500

@api_bp.route('/supported-portals', methods=['GET'])
def get_supported_portals():
    """Get list of supported job portals"""
    portals = [
        {
            'name': 'LinkedIn',
            'domain': 'linkedin.com',
            'url_example': 'https://www.linkedin.com/jobs/view/...'
        },
        {
            'name': 'Naukri',
            'domain': 'naukri.com',
            'url_example': 'https://www.naukri.com/job-...'
        },
        {
            'name': 'Indeed',
            'domain': 'indeed.com',
            'url_example': 'https://www.indeed.com/jobs?q=...'
        },
        {
            'name': 'Internshala',
            'domain': 'internshala.com',
            'url_example': 'https://internshala.com/internship/...'
        }
    ]
    
    return jsonify({
        'supported_portals': portals,
        'count': len(portals),
        'success': True
    }), 200

@api_bp.route('/test-analysis', methods=['GET'])
def test_analysis():
    """Test endpoint with sample job data"""
    analyzer = get_analyzer()
    
    sample_job = {
        'title': 'Senior Software Engineer',
        'company': 'Tech Corp',
        'company_domain': 'techcorp.com',
        'location': 'San Francisco, CA',
        'description': 'We are looking for a Senior Software Engineer with 5+ years of experience in full-stack development. You will work on challenging problems and lead a team of engineers. Requirements: Python, JavaScript, React, Node.js, Docker, Kubernetes. Salary: $150,000 - $200,000 per year.',
        'requirements': 'Python, JavaScript, React, Node.js, Docker, Kubernetes',
        'salary': '$150,000 - $200,000',
        'company_profile': 'Leading technology company',
        'job_portal': 'manual_input'
    }
    
    result = analyzer._analyze_job_data(sample_job)
    result['success'] = True
    
    return jsonify(result), 200
