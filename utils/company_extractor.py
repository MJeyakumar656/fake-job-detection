import re
from typing import List, Tuple

class CompanyExtractor:
    """Advanced company name extraction with multiple strategies"""
    
    def __init__(self):
        self.known_companies = self._load_known_companies()
        self.company_indicators = self._load_company_indicators()
    
    def _load_known_companies(self):
        """Load database of known companies"""
        return {
            'zoho': 'Zoho', 'google': 'Google', 'microsoft': 'Microsoft',
            'amazon': 'Amazon', 'apple': 'Apple', 'facebook': 'Facebook',
            'meta': 'Meta', 'netflix': 'Netflix', 'uber': 'Uber',
            'airbnb': 'Airbnb', 'tesla': 'Tesla', 'nvidia': 'NVIDIA',
            'ibm': 'IBM', 'intel': 'Intel', 'qualcomm': 'Qualcomm',
            'cisco': 'Cisco', 'oracle': 'Oracle', 'salesforce': 'Salesforce',
            'adobe': 'Adobe', 'github': 'GitHub', 'gitlab': 'GitLab',
            'stripe': 'Stripe', 'twilio': 'Twilio', 'datadog': 'Datadog',
            'cloudflare': 'Cloudflare', 'splunk': 'Splunk', 'shopify': 'Shopify',
            'slack': 'Slack', 'figma': 'Figma', 'notion': 'Notion',
            'canva': 'Canva', 'asana': 'Asana', 'monday': 'Monday.com',
            'paypal': 'PayPal', 'stripe': 'Stripe', 'square': 'Square',
            'wise': 'Wise', 'revolut': 'Revolut', 'n26': 'N26',
            'flipkart': 'Flipkart', 'myntra': 'Myntra', 'snapdeal': 'Snapdeal',
            'ola': 'Ola', 'swiggy': 'Swiggy', 'zomato': 'Zomato',
            'unacademy': 'Unacademy', 'byju': 'BYJU\'S', 'vedantu': 'Vedantu',
            'freshworks': 'Freshworks', 'infosys': 'Infosys', 'tcs': 'TCS',
            'wipro': 'Wipro', 'cognizant': 'Cognizant', 'mindtree': 'Mindtree',
            'accenture': 'Accenture', 'deloitte': 'Deloitte', 'pwc': 'PwC',
            'capgemini': 'Capgemini', 'ibm': 'IBM', 'hewlett': 'HP',
        }
    
    def _load_company_indicators(self):
        """Load company name indicators"""
        return {
            'suffixes': ['Inc', 'Ltd', 'LLC', 'Corp', 'Corporation', 'Co', 'AG',
                        'GmbH', 'SA', 'BV', 'NV', 'Pvt', 'Pte', 'AI', 'Labs',
                        'Solutions', 'Technologies', 'Services', 'Ventures', 'Group',
                        'Digital', 'Consulting', 'Research', 'Software', 'Systems'],
            'patterns': [
                r'(?:company|firm|organization|employer|hiring|posted by)\s*:\s*([A-Z][A-Za-z0-9\s&.,\'-]{2,80})',
                r'(?:at|for)\s+([A-Z][A-Za-z0-9\s&.,\'-]{2,80})(?:\s+(?:in|hiring|—|$|\n))',
            ]
        }
    
    def extract_company(self, text: str) -> str:
        """Extract company name with multiple strategies"""
        
        # Strategy 1: Known company lookup
        company = self._check_known_companies(text)
        if company:
            return company
        
        # Strategy 2: Pattern-based extraction
        company = self._extract_by_patterns(text)
        if company:
            return company
        
        # Strategy 3: Suffix-based extraction
        company = self._extract_by_suffix(text)
        if company:
            return company
        
        # Strategy 4: LinkedIn structure extraction
        company = self._extract_linkedin_structure(text)
        if company:
            return company
        
        # Strategy 5: First capitalized company-like phrase
        company = self._extract_first_company_phrase(text)
        if company:
            return company
        
        return "Unknown"
    
    def _check_known_companies(self, text: str) -> str:
        """Check if text contains known company names"""
        text_lower = text.lower()
        
        # Sort by length (longer names first to avoid partial matches)
        sorted_companies = sorted(self.known_companies.items(), 
                                 key=lambda x: len(x[0]), reverse=True)
        
        for company_lower, company_title in sorted_companies:
            # Use word boundary to avoid partial matches
            pattern = r'\b' + re.escape(company_lower) + r'\b'
            if re.search(pattern, text_lower):
                return company_title
        
        return None
    
    def _extract_by_patterns(self, text: str) -> str:
        """Extract using predefined patterns"""
        for pattern in self.company_indicators['patterns']:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                company = match.group(1).strip()
                if 2 < len(company) < 100:
                    if not self._is_noise(company):
                        return company
        
        return None
    
    def _extract_by_suffix(self, text: str) -> str:
        """Extract company names ending with known suffixes"""
        suffix_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:' + '|'.join(self.company_indicators['suffixes']) + r')\b'
        
        match = re.search(suffix_pattern, text)
        if match:
            company = match.group(1).strip()
            if not self._is_noise(company):
                return company
        
        return None
    
    def _extract_linkedin_structure(self, text: str) -> str:
        """Extract from LinkedIn job structure"""
        lines = text.split('\n')
        
        for i, line in enumerate(lines[:20]):
            line = line.strip()
            
            # Look for company on same line or nearby
            if any(keyword in line.lower() for keyword in ['developer', 'engineer', 'manager', 'analyst']):
                # Check previous line for company
                if i > 0:
                    prev_line = lines[i-1].strip()
                    if prev_line and prev_line[0].isupper() and not self._is_noise(prev_line):
                        if 2 < len(prev_line) < 80:
                            return prev_line
        
        return None
    
    def _extract_first_company_phrase(self, text: str) -> str:
        """Extract first valid company-like phrase"""
        lines = text.split('\n')
        
        for line in lines[:15]:
            line = line.strip()
            
            if not line or len(line) < 3 or len(line) > 100:
                continue
            
            # Skip noise patterns
            if self._is_noise(line):
                continue
            
            # Check if looks like company name
            if line[0].isupper() and re.match(r'^[A-Z][A-Za-z0-9\s&.,\'-]+$', line):
                if line.count(' ') <= 4:  # Max 4 words
                    return line
        
        return None
    
    def _is_noise(self, text: str) -> bool:
        """Check if text is noise (navigation, UI elements, etc.)"""
        noise_keywords = [
            'role', 'position', 'job', 'hiring', 'apply', 'requirements',
            'about', 'responsibilities', 'qualification', 'skills', 'benefits',
            'experience', 'senior', 'junior', 'find', 'search', 'sign', 'upload',
            'expand', 'button', 'displays', 'selected', 'message', 'chat',
            'click', 'link', 'verify', 'confirmation', 'verify', 'password',
            'email', 'phone', 'contact', 'whatsapp', 'telegram', 'dm',
            'use ai', 'artificial intelligence', 'machine learning', 'data science'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in noise_keywords)