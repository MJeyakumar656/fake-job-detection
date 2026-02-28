import os

class Config:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    
    # Model paths
    MODEL_PATH = os.path.join('models', 'fake_job_detector.h5')
    VECTORIZER_PATH = os.path.join('models', 'tfidf_vectorizer.pkl')
    
    # Scraping config
    SCRAPING_TIMEOUT = 10
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    # Job portals
    SUPPORTED_PORTALS = [
        'linkedin.com',
        'naukri.com',
        'indeed.com',
        'internshala.com'
    ]

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
