import re
import validators
from datetime import datetime

class JobValidator:
    """Validate job data and URLs"""
    
    @staticmethod
    def is_valid_url(url):
        """Validate URL format"""
        return validators.url(url) is True
    
    @staticmethod
    def is_valid_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def extract_emails(text):
        """Extract all emails from text"""
        pattern = r'\S+@\S+\.\S+'
        return re.findall(pattern, text)
    
    @staticmethod
    def is_supported_portal(url):
        """Check if URL is from supported job portal"""
        supported = ['linkedin.com', 'naukri.com', 'indeed.com', 
                     'internshala.com']
        return any(portal in url.lower() for portal in supported)

class TextProcessor:
    """Process and clean text"""
    
    @staticmethod
    def truncate(text, max_length=500):
        """Truncate text to max length"""
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text
    
    @staticmethod
    def count_words(text):
        """Count words in text"""
        return len(text.split())
    
    @staticmethod
    def get_word_frequency(text):
        """Get word frequency dictionary"""
        words = text.lower().split()
        freq = {}
        for word in words:
            freq[word] = freq.get(word, 0) + 1
        return sorted(freq.items(), key=lambda x: x[1], reverse=True)

class LogManager:
    """Manage logging"""
    
    @staticmethod
    def log_analysis(job_title, portal, prediction):
        """Log job analysis"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] Job: {job_title} | Portal: {portal} | Prediction: {prediction}"
        
        with open('logs/analysis.log', 'a') as f:
            f.write(log_entry + '\n')
