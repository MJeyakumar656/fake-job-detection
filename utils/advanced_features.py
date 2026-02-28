import re
import numpy as np

class AdvancedFeatureExtractor:
    """Extract advanced linguistic features for scam detection"""
    
    def __init__(self):
        self.scam_keywords = self._load_scam_keywords()
        self.legitimate_keywords = self._load_legitimate_keywords()
    
    def _load_scam_keywords(self):
        """Known scam indicators"""
        return {
            'money_urgency': ['urgent', 'asap', 'immediately', 'hurry', 'act now', 'limited time', 'dont miss', 'deadline'],
            'unrealistic_pay': ['easy money', 'fast money', 'guaranteed income', 'passive income', 'earn $', '₹'],
            'no_verification': ['no interview', 'no verification', 'no background check', 'instant hire', 'no assessment'],
            'payment_request': ['payment required', 'deposit', 'registration fee', 'processing fee', 'upfront'],
            'communication_red_flags': ['whatsapp', 'telegram', 'dm only', 'message for details'],
            'vague_terms': ['exciting opportunity', 'work from anywhere', 'flexible', 'easy', 'simple'],
        }
    
    def _load_legitimate_keywords(self):
        """Known legitimate indicators"""
        return {
            'professional': ['responsibilities', 'qualifications', 'requirements', 'benefits', 'salary', 'ctc', 'package'],
            'company_info': ['about us', 'company', 'organization', 'industry', 'years in business'],
            'detailed_job': ['description', 'duties', 'tasks', 'skills required', 'experience'],
            'benefits': ['insurance', 'health', '401k', 'pto', 'leave', 'bonus', 'commission'],
        }
    
    def extract_features(self, text):
        """Extract all advanced features"""
        features = {}
        text_lower = text.lower()
        
        # Scam indicators score
        scam_score = 0
        for category, keywords in self.scam_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scam_score += 1
        
        # Legitimate indicators score
        legit_score = 0
        for category, keywords in self.legitimate_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    legit_score += 1
        
        features['scam_score'] = scam_score
        features['legit_score'] = legit_score
        features['ratio'] = scam_score / max(legit_score, 1)
        
        # Linguistic features
        words = text.split()
        features['avg_word_length'] = np.mean([len(w) for w in words]) if words else 0
        features['sentence_count'] = len(re.split(r'[.!?]+', text))
        features['caps_ratio'] = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        features['punctuation_ratio'] = sum(1 for c in text if c in '!?') / max(len(text), 1)
        
        # Professionalism
        features['has_email'] = 1 if re.search(r'[\w\.-]+@[\w\.-]+', text) else 0
        features['has_phone'] = 1 if re.search(r'\+?\d{10,}', text) else 0
        features['has_url'] = 1 if re.search(r'http[s]?://', text) else 0
        
        # Text length
        features['text_length'] = len(text)
        features['word_count'] = len(words)
        
        return features