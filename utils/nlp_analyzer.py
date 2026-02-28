import re

class NLPAnalyzer:
    """Advanced NLP analysis for job postings"""
    
    @staticmethod
    def analyze_sentiment(text):
        """Analyze sentiment of text using simple rule-based approach"""
        try:
            # Simple sentiment analysis without TextBlob
            positive_words = ['excellent', 'great', 'amazing', 'wonderful', 'fantastic', 'best', 'good']
            negative_words = ['bad', 'terrible', 'awful', 'poor', 'worst', 'horrible', 'scam']
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            polarity = (positive_count - negative_count) / max(positive_count + negative_count, 1)
            
            return {
                'polarity': polarity,
                'subjectivity': 0.5,
                'sentiment': 'Positive' if polarity > 0.1 else 'Negative' if polarity < -0.1 else 'Neutral'
            }
        except:
            return {'polarity': 0, 'subjectivity': 0.5, 'sentiment': 'Unknown'}
    
    @staticmethod
    def check_professionalism(text):
        """Check professionalism of text"""
        scores = {}
        
        # Grammar and spelling
        errors = 0
        common_misspellings = ['heelo', 'wel come', 'succesful', 'recieve', 'occassion']
        for misspelling in common_misspellings:
            errors += text.lower().count(misspelling)
        
        scores['grammar_errors'] = errors
        
        # Professional vocabulary
        professional_words = ['implement', 'develop', 'design', 'manage', 'coordinate', 'maintain']
        prof_count = sum(1 for word in professional_words if word in text.lower())
        scores['professional_vocabulary'] = prof_count
        
        # Unprofessional words
        unprofessional = ['lol', 'btw', 'omg', 'gonna', 'wanna', 'ur', 'u ', 'thx']
        unprof_count = sum(1 for word in unprofessional if word in text.lower())
        scores['unprofessional_vocabulary'] = unprof_count
        
        # Calculate professionalism score (0-100)
        prof_score = 100 - (errors * 10) - (unprof_count * 15) + (prof_count * 5)
        scores['professionalism_score'] = max(0, min(100, prof_score))
        
        return scores
    
    @staticmethod
    def extract_entities(text):
        """Extract important entities from text"""
        entities = {}
        
        # Email addresses
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        entities['emails'] = emails
        
        # Phone numbers
        phones = re.findall(r'\+?\d[\d\s\-\.]{8,}', text)
        entities['phones'] = phones
        
        # URLs
        urls = re.findall(r'http[s]?://\S+', text)
        entities['urls'] = urls
        
        # Currency amounts
        amounts = re.findall(r'[\$₹€]\s*[\d,]+(?:\.\d{2})?', text)
        entities['amounts'] = amounts
        
        return entities