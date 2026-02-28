"""Tests for feature extraction and red flag detection."""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.red_flags import count_red_flags, analyze_quality, categorize_severity
from src.feature_extractor import FeatureExtractor


class TestRedFlagDetection:
    """Test red flag detection module."""

    def test_detects_urgency_language(self):
        """Should detect urgency language as a red flag."""
        text = "URGENT hiring! Apply NOW before it's too late! Limited positions available! Act now!"
        score, flags = count_red_flags(text)
        assert score > 0

    def test_detects_money_requests(self):
        """Should detect payment requests as a red flag."""
        text = "Pay a small registration fee of $50 to secure your spot. Upfront payment required."
        score, flags = count_red_flags(text)
        assert score > 0

    def test_detects_free_email(self):
        """Should detect free email domains as a red flag."""
        text = "Contact us at hiring.manager@gmail.com. WhatsApp for details. DM for details."
        score, flags = count_red_flags(text)
        assert score > 0

    def test_detects_unrealistic_salary(self):
        """Should detect unrealistic salary promises."""
        text = "Earn $5000 per week with no experience needed! Guaranteed income! Make money fast!"
        score, flags = count_red_flags(text)
        assert score > 0

    def test_legitimate_job_has_few_flags(self):
        """A well-written job posting should have a low score."""
        text = """
        Senior Software Engineer at Tech Corp.
        Location: San Francisco, CA.
        Salary: $150,000 - $200,000 per year.
        Requirements: 5+ years of experience in Python, JavaScript.
        Responsibilities: Design and implement scalable systems.
        Benefits: Health insurance, 401k, PTO.
        Apply at careers@techcorp.com.
        """
        score, flags = count_red_flags(text)
        assert score <= 5  # Should be low

    def test_fake_job_has_many_flags(self, sample_fake_job_text):
        """A fake job posting should trigger a high score."""
        score, flags = count_red_flags(sample_fake_job_text)
        assert score >= 3


class TestQualityAnalysis:
    """Test quality analysis functions."""

    def test_quality_returns_string(self):
        """analyze_quality should return a quality level string."""
        result = analyze_quality("This is a sample job description for testing purposes with enough text to analyze properly.")
        assert isinstance(result, str)
        assert result in ["FAKE - SCAM", "SUSPICIOUS", "Questionable", "High", "Medium", "Low", "Very Low"]

    def test_severity_categorization(self):
        """categorize_severity should return valid severity levels."""
        assert categorize_severity(0) == "NONE"
        assert categorize_severity(1) == "LOW"
        assert categorize_severity(5) == "MEDIUM"
        assert categorize_severity(8) == "HIGH"
        assert categorize_severity(15) == "CRITICAL"


class TestFeatureExtractor:
    """Test feature extraction."""

    @pytest.fixture
    def extractor(self):
        return FeatureExtractor()

    def test_clean_text(self, extractor):
        """clean_text should normalize text."""
        result = extractor.clean_text("Hello   WORLD!!!  \n\n Test")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_clean_text_handles_empty(self, extractor):
        """clean_text should handle empty strings."""
        result = extractor.clean_text("")
        assert isinstance(result, str)

    def test_extract_text_features(self, extractor):
        """Should extract text features from job description."""
        text = "This is a sample job description with several words for testing feature extraction."
        features = extractor.extract_text_features(text)
        assert isinstance(features, dict)

    def test_extract_red_flags(self, extractor):
        """Should extract red flags from job posting."""
        description = "URGENT! No experience needed. Pay registration fee. Contact gmail.com"
        flags = extractor.extract_red_flags(description, "", "")
        assert isinstance(flags, (list, dict, tuple))

    def test_extract_all_features(self, extractor, sample_job_data):
        """Should extract all features from structured job data."""
        features, combined_text = extractor.extract_all_features(sample_job_data)
        assert isinstance(features, dict)
        assert isinstance(combined_text, str)
        assert 'text_length' in features
        assert 'word_count' in features
        assert 'red_flag_count' in features

    def test_feature_values_reasonable(self, extractor, sample_job_data):
        """Feature values should be reasonable numbers."""
        features, _ = extractor.extract_all_features(sample_job_data)
        assert features['text_length'] >= 0
        assert features['word_count'] >= 0
        assert features['spelling_errors'] >= 0
        assert 0 <= features['uppercase_ratio'] <= 1
        assert 0 <= features['digit_ratio'] <= 1

    def test_spelling_features(self, extractor):
        """Should detect spelling quality."""
        features = extractor.extract_spelling_features("This is a well written sentence.")
        assert isinstance(features, dict)
