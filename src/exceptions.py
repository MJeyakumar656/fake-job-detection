class FakeJobDetectionException(Exception):
    """Base exception for fake job detection"""
    pass

class ScraperException(FakeJobDetectionException):
    """Exception during web scraping"""
    pass

class ModelException(FakeJobDetectionException):
    """Exception during model prediction"""
    pass

class AnalysisException(FakeJobDetectionException):
    """Exception during job analysis"""
    pass

class ValidationException(FakeJobDetectionException):
    """Exception during data validation"""
    pass