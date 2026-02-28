import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app


@pytest.fixture
def app():
    """Create application for testing."""
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
    })
    yield flask_app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def sample_job_text():
    """Sample legitimate job posting text."""
    return """
    Senior Software Engineer - Tech Corp Inc.
    
    Location: San Francisco, CA
    Salary: $150,000 - $200,000 per year
    
    About the Company:
    Tech Corp Inc. is a leading technology company specializing in cloud computing 
    and enterprise software solutions. Founded in 2010, we serve over 500 Fortune 1000 clients.
    
    Job Description:
    We are looking for a Senior Software Engineer with 5+ years of experience in full-stack 
    development. You will work on challenging problems and lead a team of engineers building 
    our next-generation platform.
    
    Responsibilities:
    - Design and implement scalable microservices architecture
    - Lead code reviews and mentor junior developers
    - Collaborate with product managers to define technical requirements
    - Write comprehensive unit and integration tests
    - Participate in on-call rotation for production systems
    
    Requirements:
    - BS/MS in Computer Science or equivalent experience
    - 5+ years of experience with Python, JavaScript, or Go
    - Experience with React, Node.js, Docker, Kubernetes
    - Strong understanding of distributed systems
    - Excellent communication and teamwork skills
    
    Benefits:
    - Competitive salary and equity
    - Health, dental, and vision insurance
    - 401(k) with company match
    - Flexible work arrangements
    - Professional development budget
    
    Apply at: careers@techcorp.com
    Company website: www.techcorp.com
    """


@pytest.fixture
def sample_fake_job_text():
    """Sample suspicious/fake job posting text."""
    return """
    URGENT HIRING!!! Work From Home - Earn $5000/week!!!
    
    NO EXPERIENCE NEEDED! START IMMEDIATELY!
    
    We are hiring data entry operators. You can earn up to $5000 per week 
    working from the comfort of your home! This is a once in a lifetime opportunity!
    
    Requirements: NONE! Anyone can apply!
    
    Just send your bank details and social security number to get started.
    Pay a small registration fee of $50 to secure your spot.
    
    Contact: hiring.manager123@gmail.com
    WhatsApp: +1-555-0123
    
    Limited spots available! Apply NOW before it's too late!
    Don't miss this amazing opportunity to make money fast!
    """


@pytest.fixture
def sample_job_data():
    """Structured job data for testing."""
    return {
        'title': 'Senior Software Engineer',
        'company': 'Tech Corp',
        'company_domain': 'techcorp.com',
        'location': 'San Francisco, CA',
        'description': 'We are looking for a Senior Software Engineer with 5+ years of experience.',
        'requirements': 'Python, JavaScript, React, Node.js, Docker, Kubernetes',
        'salary': '$150,000 - $200,000',
        'company_profile': 'Leading technology company',
        'job_portal': 'manual_input'
    }
