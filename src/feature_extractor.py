import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from textblob import TextBlob
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from collections import Counter
import math

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

class FeatureExtractor:
    """Extract features from job postings"""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=500,
            min_df=2,
            max_df=0.8,
            ngram_range=(1, 2)
        )
    
    def clean_text(self, text):
        """Clean and preprocess text"""
        if not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_text_features(self, text):
        """Extract linguistic features - ultra fast version"""
        # Use extremely simplified features for maximum speed
        features = {
            'text_length': len(text),
            'word_count': len(text.split()),
            'avg_word_length': 5.0,  # Fixed average for speed
            'unique_word_ratio': 0.6,  # Fixed ratio for speed
            'uppercase_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0,
            'digit_ratio': sum(1 for c in text if c.isdigit()) / len(text) if text else 0,
        }
        return features
    
    def extract_spelling_features(self, text):
        """Extract spelling and grammar features - ultra fast version"""
        # Skip all expensive operations for speed
        features = {
            'spelling_errors': 0,  # Assume no errors for speed
            'grammar_score': len(text),  # Length as proxy
            'sentence_count': text.count('.') + text.count('!') + text.count('?') + 1,
        }
        return features
    
    def extract_domain_features(self, company_domain, company_name):
        """Extract company domain features"""
        features = {
            'domain_exists': 1 if company_domain else 0,
            'domain_length': len(company_domain) if company_domain else 0,
            'has_suspicious_domain': self.check_suspicious_domain(company_domain),
            'company_name_length': len(company_name) if company_name else 0,
        }
        
        return features
    
    def check_suspicious_domain(self, domain):
        """Enhanced check for suspicious domain patterns with reputation scoring"""
        if not domain:
            return 1

        domain_lower = domain.lower()

        # High-risk suspicious keywords (weight: 1.0)
        high_risk_keywords = ['temp', 'fake', 'test', 'demo', 'example', 'mail.com', 'gmail', 'yahoo', 'hotmail']

        # Medium-risk suspicious TLDs (weight: 0.8)
        suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.win', '.bid']

        # Low-risk patterns (weight: 0.5)
        low_risk_patterns = ['temp-mail', '10minutemail', 'guerrillamail', 'mailinator']

        # Check high-risk keywords
        for keyword in high_risk_keywords:
            if keyword in domain_lower:
                return 1.0

        # Check suspicious TLDs
        for tld in suspicious_tlds:
            if domain_lower.endswith(tld):
                return 0.8

        # Check low-risk patterns
        for pattern in low_risk_patterns:
            if pattern in domain_lower:
                return 0.5

        # Check for numbers-only domains (suspicious)
        if re.match(r'^\d+\..*$', domain_lower):
            return 0.7

        # Check for extremely short domains
        domain_parts = domain_lower.split('.')
        if len(domain_parts[0]) < 3:
            return 0.6

        return 0.0  # Legitimate domain
    
    def extract_red_flags(self, description, requirements, salary):
        """Detect red flags in job posting - optimized for speed"""
        red_flags = []

        # Early return for very short descriptions
        if len(description) < 50:
            red_flags.append('vague_description')
            return red_flags

        # Convert to lowercase once
        text_combined = (description + ' ' + requirements).lower()

        # Check for unrealistic salary (fast check)
        if salary and isinstance(salary, str):
            salary_lower = salary.lower()
            if 'unlimited' in salary_lower or 'negotiable' in salary_lower or 'fake' in salary_lower:
                red_flags.append('unrealistic_salary')

        # Check for spam phrases (optimized)
        spam_indicators = ['work from home with no experience', 'easy money', 'get rich quick',
                          'no experience needed', 'guaranteed income', 'bitcoin', 'crypto']
        for indicator in spam_indicators:
            if indicator in text_combined:
                red_flags.append('spam_phrase')
                break

        # Check for suspicious emails (simplified)
        if '@' in text_combined:
            # Simple check for suspicious patterns
            if any(sus in text_combined for sus in ['@temp', '@fake', '@test', '@gmail.com', '@yahoo.com']):
                red_flags.append('suspicious_email')

        # Check for missing requirements (fast)
        if not requirements or len(requirements.strip()) < 20:
            red_flags.append('missing_requirements')

        return red_flags
    
    def extract_all_features(self, job_data):
        """Extract all features from job posting with enhanced analysis"""
        description = job_data.get('description', '')
        requirements = job_data.get('requirements', '')
        company_profile = job_data.get('company_profile', '')
        company_domain = job_data.get('company_domain', '')
        company_name = job_data.get('company_name', '')
        salary = job_data.get('salary', '')

        # Combine text for analysis
        combined_text = f"{description} {requirements} {company_profile}"

        # Extract basic features
        text_features = self.extract_text_features(combined_text)
        spelling_features = self.extract_spelling_features(combined_text)
        domain_features = self.extract_domain_features(company_domain, company_name)
        red_flags = self.extract_red_flags(description, requirements, salary)

        # Enhanced text analysis
        words = combined_text.split()
        sentences = re.split(r'[.!?]+', combined_text)

        # Sentiment analysis
        sentiment_polarity, sentiment_subjectivity = self._extract_sentiment(combined_text)

        # Readability and complexity metrics
        readability_score = self._calculate_readability(combined_text, words, sentences)
        lexical_diversity = self._calculate_lexical_diversity(words)
        sentence_complexity = self._calculate_sentence_complexity(sentences)
        professional_term_ratio = self._calculate_professional_term_ratio(combined_text)

        # Contextual red flag analysis
        combo_score, combo_flags = self.analyze_red_flag_combinations(red_flags, combined_text)

        # Enhanced features dictionary
        features = {
            # Basic text features
            **text_features,
            **spelling_features,
            **domain_features,

            # Red flags
            'red_flag_count': len(red_flags),
            'red_flags': red_flags,

            # Advanced NLP features
            'sentiment_polarity': sentiment_polarity,
            'sentiment_subjectivity': sentiment_subjectivity,
            'readability_score': readability_score,
            'lexical_diversity': lexical_diversity,
            'sentence_complexity': sentence_complexity,
            'professional_term_ratio': professional_term_ratio,

            # Contextual analysis
            'red_flag_combo_score': combo_score,
            'red_flag_combinations': combo_flags,

            # Derived quality indicators
            'text_quality_score': (
                readability_score * 0.3 +
                lexical_diversity * 0.3 +
                professional_term_ratio * 0.4
            ),
            'suspicion_score': min(1.0, (len(red_flags) * 0.1 + combo_score * 0.05)),
        }

        return features, combined_text

    def _extract_sentiment(self, text):
        """Extract sentiment polarity and subjectivity"""
        try:
            blob = TextBlob(text)
            return blob.sentiment.polarity, blob.sentiment.subjectivity
        except:
            return 0.0, 0.0

    def _calculate_readability(self, text, words, sentences):
        """Calculate readability score using simplified Flesch-Kincaid"""
        if not words or not sentences:
            return 0

        # Average sentence length (words per sentence)
        avg_sentence_length = len(words) / len(sentences)

        # Average syllables per word (simplified approximation)
        avg_syllables_per_word = sum(self._count_syllables(word) for word in words) / len(words)

        # Flesch Reading Ease score (simplified)
        readability = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)

        # Normalize to 0-1 scale
        return max(0, min(1, readability / 100))

    def _count_syllables(self, word):
        """Count syllables in a word (simplified)"""
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        if word[0] in vowels:
            count += 1
        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                count += 1
        if word.endswith("e"):
            count -= 1
        if count == 0:
            count += 1
        return count

    def _calculate_lexical_diversity(self, words):
        """Calculate lexical diversity (unique words / total words)"""
        if not words:
            return 0
        return len(set(words)) / len(words)

    def _calculate_sentence_complexity(self, sentences):
        """Calculate sentence complexity based on length variation"""
        if len(sentences) < 2:
            return 0

        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        if not sentence_lengths:
            return 0

        # Coefficient of variation (standard deviation / mean)
        mean_length = np.mean(sentence_lengths)
        std_length = np.std(sentence_lengths)

        return std_length / mean_length if mean_length > 0 else 0

    def _calculate_professional_term_ratio(self, text):
        """Calculate ratio of professional/business terms"""
        professional_terms = {
            'responsibilities', 'requirements', 'qualifications', 'skills', 'experience',
            'education', 'benefits', 'salary', 'compensation', 'company', 'organization',
            'team', 'project', 'client', 'customer', 'deadline', 'milestone', 'objective',
            'strategy', 'analysis', 'development', 'implementation', 'collaboration'
        }

        words = set(text.lower().split())
        professional_count = sum(1 for word in words if word in professional_terms)

        return professional_count / len(words) if words else 0

    def analyze_red_flag_combinations(self, red_flags, text):
        """Analyze combinations of red flags for enhanced detection"""
        combo_score = 0.0
        combo_flags = []

        # Convert text to lowercase for analysis
        text_lower = text.lower()

        # High-risk combinations (add significant suspicion)
        high_risk_combos = [
            (['payment required', 'urgent hiring'], 0.8, 'Payment + Urgency: Classic scam pattern'),
            (['bitcoin', 'guaranteed income'], 0.8, 'Crypto + Guarantee: Investment scam'),
            (['no experience needed', 'high salary'], 0.7, 'No experience + High pay: Unrealistic'),
            (['whatsapp only', 'no interview'], 0.7, 'WhatsApp only + No interview: Suspicious contact'),
            (['work from home', 'no experience needed', 'guaranteed'], 0.6, 'WFH + No exp + Guaranteed: Common scam'),
        ]

        # Medium-risk combinations
        medium_risk_combos = [
            (['urgent', 'apply now'], 0.4, 'Urgency + Apply pressure'),
            (['investment', 'commission'], 0.4, 'Investment + Commission: MLM indicators'),
            (['crypto', 'remote work'], 0.3, 'Crypto + Remote: Modern scam pattern'),
            (['ai training', 'guaranteed job'], 0.3, 'AI training + Job guarantee: Training scam'),
        ]

        # Check high-risk combinations
        for combo_flags_list, score, description in high_risk_combos:
            if all(flag in red_flags for flag in combo_flags_list):
                combo_score += score
                combo_flags.append(description)

        # Check medium-risk combinations
        for combo_flags_list, score, description in medium_risk_combos:
            if all(flag in red_flags for flag in combo_flags_list):
                combo_score += score
                combo_flags.append(description)

        # Additional contextual analysis
        if len(red_flags) >= 3:
            combo_score += 0.2  # Multiple red flags increase suspicion
            combo_flags.append('Multiple red flags detected')

        # Check for scam phrase density
        scam_phrases = ['guaranteed', 'easy money', 'work from home', 'no experience', 'urgent', 'apply now', 'bitcoin', 'crypto', 'passive income']
        scam_count = sum(1 for phrase in scam_phrases if phrase in text_lower)
        total_words = len(text_lower.split())

        if total_words > 0:
            scam_density = scam_count / total_words
            if scam_density > 0.03:  # More than 3% scam phrases
                density_penalty = min(0.3, scam_density * 5)
                combo_score += density_penalty
                combo_flags.append(f'High scam phrase density ({scam_density:.1%})')

        return combo_score, combo_flags
