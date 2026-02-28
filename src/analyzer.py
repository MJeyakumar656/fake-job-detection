import numpy as np
from pathlib import Path
from src.model_trainer import FakeJobDetector
from src.feature_extractor import FeatureExtractor
from src.scrapers.scraper_manager import ScraperManager
from utils.red_flags import count_red_flags, analyze_quality
from utils.domain_check import (
    get_company_domain, 
    extract_domain_from_url,
    is_suspicious_domain,
    check_domain_reputation,
    verify_company_legitimacy,
    analyze_domain_complete
)

class JobAnalyzer:
    """Main analysis engine for fake job detection"""
    
    def __init__(self):
        self.detector = FakeJobDetector()
        self.feature_extractor = FeatureExtractor()
        
        # Load trained model
        try:
            self.detector.load_model()
            self.model_loaded = True
            print("[OK] AI Model loaded successfully")
        except Exception as e:
            print(f"[WARN] Model not found: {str(e)}")
            print("[WARN] Running in demo mode without trained model")
            self.model_loaded = False
    
    def analyze_from_url(self, url):
        """Analyze job from URL"""
        print(f"\n[INFO] Analyzing job from URL: {url}")
        
        try:
            # Step 1: Scrape job data
            print("[1/3] Scraping job data...")
            job_data = ScraperManager.scrape(url)
            print("✓ Job data scraped successfully")
            
            # Step 2: Analyze job posting
            print("[2/3] Running AI analysis...")
            analysis_result, features = self._analyze_job_data(job_data)

            # Step 3: Generate quality score
            print("[3/3] Generating quality assessment...")
            analysis_result['job_quality'] = self._assess_job_quality(analysis_result, features)
            
            print("[OK] Analysis completed")
            return analysis_result
            
        except Exception as e:
            return {
                'error': f"Failed to analyze job: {str(e)}",
                'success': False
            }
    
    def analyze_from_text(self, job_description_text):
        """Analyze job from pasted text"""
        print(f"\n[INFO] Analyzing job from pasted text")
        
        try:
            # Parse job description text to extract structured data
            print("[1/3] Parsing job description...")
            job_data = self._parse_job_text(job_description_text)
            print("✓ Job data parsed successfully")
            
            # Step 2: Analyze job posting
            print("[2/3] Running AI analysis...")
            analysis_result, features = self._analyze_job_data(job_data)

            # Step 3: Generate quality score
            print("[3/3] Generating quality assessment...")
            analysis_result['job_quality'] = self._assess_job_quality(analysis_result, features)
            
            print("[OK] Analysis completed")
            return analysis_result
            
        except Exception as e:
            return {
                'error': f"Failed to analyze job: {str(e)}",
                'success': False
            }
    
    def _parse_job_text(self, job_description_text):
        """Parse job description text into structured data - enhanced extraction"""
        text = job_description_text.strip()
        lines = text.split('\n')

        job_data = {
            'title': self._extract_title_enhanced(text, lines),
            'company': self._extract_company_enhanced(text, lines),
            'company_domain': self._extract_domain(lines),
            'location': self._extract_location(lines),
            'description': text,
            'requirements': self._extract_requirements(lines),
            'salary': self._extract_salary(lines),
            'company_profile': '',
            'job_type': '',
            'job_portal': self._detect_job_portal(text),
            'url': 'N/A'
        }

        return job_data
    
    def _extract_title(self, lines):
        """Extract job title from text"""
        # Usually first non-empty line or contains "Title"
        for line in lines[:5]:
            if line.strip() and len(line) < 100:
                return line.strip()
        return "Unknown Job Title"

    def _extract_title_enhanced(self, text, lines):
        """Enhanced job title extraction with pattern recognition"""
        # Look for explicit patterns first
        import re

        # Pattern 1: Job Title: [Title]
        title_match = re.search(r'Job Title:\s*([^\n\r]+)', text, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()

        # Pattern 2: Role: [Title]
        role_match = re.search(r'Role:\s*([^\n\r]+)', text, re.IGNORECASE)
        if role_match:
            return role_match.group(1).strip()

        # Pattern 3: About the job: [Title]
        about_match = re.search(r'About the job:\s*([^\n\r]+)', text, re.IGNORECASE)
        if about_match:
            return about_match.group(1).strip()

        # Pattern 4: Look for job titles in structured formats
        job_title_patterns = [
            r'\b(Software Engineer|DevOps Engineer|Cloud Engineer|Data Engineer|Product Manager|Engineering Manager|Senior Software Engineer|Principal Engineer|Staff Engineer|Technical Lead|Team Lead|Engineering Lead|Site Reliability Engineer|Infrastructure Engineer|Security Engineer|Backend Engineer|Frontend Engineer|Full Stack Engineer|Mobile Engineer|iOS Engineer|Android Engineer|QA Engineer|Test Engineer|Automation Engineer|Release Engineer|Build Engineer|Platform Engineer|Systems Engineer|Network Engineer|Database Engineer|Data Scientist|Machine Learning Engineer|AI Engineer|Research Scientist|Technical Program Manager|Product Engineer|Solutions Engineer|Customer Engineer|Cloud Architect|Systems Architect|Software Architect|Technical Architect|Principal Architect|Staff Architect)\b\s*[-–—]?\s*\b(Senior|Principal|Staff|Lead|Manager|Director|VP|Head|Chief)?\b',
            r'\b(Developer|Engineer|Scientist|Analyst|Manager|Architect|Specialist|Administrator|Coordinator|Consultant)\b\s+\b(in|for|of)\b\s+(.{10,50})',
            r'(.{15,80})\s+\b(Engineer|Developer|Scientist|Manager|Architect|Specialist|Administrator)\b'
        ]

        for pattern in job_title_patterns:
            title_match = re.search(pattern, text, re.IGNORECASE)
            if title_match:
                title = title_match.group(0).strip()
                title = re.sub(r'\s+', ' ', title)
                title = re.sub(r'[.,;:!?]+$', '', title)
                if 10 <= len(title) <= 100:
                    return title

        # Pattern 5: Special handling for tech job postings
        if 'experience in' in text.lower():
            experience_patterns = [
                r'experience in\s+([^.]+?)\s*(?:integration|delivery|provisioning|infrastructure)',
                r'experience in\s+([^.]+?)\s*(?:engineer|developer|scientist|manager|architect)',
                r'experience in\s+([^.]+?)\s*(?:and|or|,|\.)'
            ]
            for pattern in experience_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    potential_title = match.group(1).strip()
                    if any(term in potential_title.lower() for term in ['engineer', 'developer', 'scientist', 'architect', 'manager']):
                        potential_title = re.sub(r'\s+', ' ', potential_title)
                        potential_title = re.sub(r'^(in|for|of|and|or)\s+', '', potential_title, flags=re.IGNORECASE)
                        if 5 <= len(potential_title) <= 80:
                            return potential_title.title()

        # Pattern 6: Look for repeated lines (likely job title)
        title_counts = {}
        for line in lines[:15]:
            line = line.strip()
            if line and len(line) > 3 and len(line) < 100:
                skip_patterns = ['company logo', 'duration', 'month', 'remote', 'hiring office', 'applied', 'internship highlights', 'description', 'key responsibilities', 'skill', 'preferred candidate', 'industry type', 'department', 'employment type', 'education', 'key skills', 'report this job', 'about company', 'company info', 'address', 'minimum qualifications', 'preferred qualifications', 'responsibilities include', 'you will', 'what you will do']
                if any(pattern in line.lower() for pattern in skip_patterns):
                    continue
                if '@' not in line and 'http' not in line and not line.startswith('₹') and not line.startswith('$'):
                    title_counts[line] = title_counts.get(line, 0) + 1

        if title_counts:
            most_common = max(title_counts.items(), key=lambda x: x[1])
            if most_common[1] >= 2:
                return most_common[0]

        # Pattern 7: Look for common job title indicators
        for line in lines[:10]:
            line = line.strip()
            if not line:
                continue
            skip_indicators = ['about', 'company', 'location', 'salary', 'requirements', 'qualifications', 'responsibilities', 'benefits', 'minimum', 'preferred', 'experience', 'skills', 'education']
            if any(line.lower().startswith(indicator) for indicator in skip_indicators):
                continue
            if 3 < len(line) < 100 and '@' not in line and 'http' not in line:
                return line

        # Fallback to original method
        return self._extract_title(lines)

    def _extract_company(self, lines):
        """Extract company name from text"""
        for line in lines:
            if 'company' in line.lower() or 'employer' in line.lower():
                return line.split(':')[-1].strip()
        return "Unknown Company"

    def _extract_company_enhanced(self, text, lines):
        """Enhanced company name extraction with pattern recognition"""
        import re

        # Pattern 0: Detect major tech companies from content patterns
        text_lower = text.lower()
        if 'google' in text_lower and ('cloud' in text_lower or 'android' in text_lower or 'kubernetes' in text_lower or 'tensorflow' in text_lower or 'computer science' in text_lower):
            return 'Google'
        elif 'microsoft' in text_lower and ('azure' in text_lower or 'office' in text_lower or '.net' in text_lower):
            return 'Microsoft'
        elif 'amazon' in text_lower and ('aws' in text_lower or 'alexa' in text_lower):
            return 'Amazon'
        elif 'meta' in text_lower or 'facebook' in text_lower:
            return 'Meta'
        elif 'apple' in text_lower and ('ios' in text_lower or 'macos' in text_lower):
            return 'Apple'
        elif 'netflix' in text_lower:
            return 'Netflix'
        elif 'uber' in text_lower:
            return 'Uber'
        elif 'airbnb' in text_lower:
            return 'Airbnb'

        # Pattern 1: About company section
        about_company_match = re.search(r'About company\s*[:.-]?\s*([^\n\r]+)', text, re.IGNORECASE)
        if about_company_match:
            company = about_company_match.group(1).strip()
            company = re.split(r'[-–—]', company)[0].strip()
            if len(company) > 50:
                company_patterns = [
                    r'^([A-Z][a-zA-Z\s]+(?:Inc|Ltd|Corp|LLC|Technologies|Solutions|Systems))\s',
                    r'^([A-Z][a-zA-Z\s]+(?:Inc|Ltd|Corp|LLC))\.',
                    r'^([A-Z][a-zA-Z\s]+),\s+Inc\.'
                ]
                for pattern in company_patterns:
                    match = re.search(pattern, company)
                    if match:
                        return match.group(1).strip()
                words = company.split()[:5]
                company_candidate = ' '.join(words)
                if any(keyword in company_candidate.lower() for keyword in ['inc', 'ltd', 'corp', 'llc', 'technologies', 'solutions']):
                    return company_candidate
            elif len(company) > 3 and not company.lower().startswith(('india', 'funded', 'in collaboration')):
                return company

        # Pattern 2: Company Name: [Company]
        company_match = re.search(r'Company Name:\s*([^\n\r]+)', text, re.IGNORECASE)
        if company_match:
            return company_match.group(1).strip()

        # Pattern 3: Company: [Company]
        company_match2 = re.search(r'Company:\s*([^\n\r]+)', text, re.IGNORECASE)
        if company_match2:
            return company_match2.group(1).strip()

        # Pattern 4: Look for repeated company names in first few lines
        company_counts = {}
        for line in lines[:12]:
            line = line.strip()
            if line and len(line) > 3 and len(line) < 50:
                skip_patterns = ['company logo', 'duration', 'month', 'remote', 'hiring office', 'applied', 'internship highlights', 'description', 'key responsibilities', 'skill', 'preferred candidate', 'industry type', 'department', 'employment type', 'education', 'key skills', 'report this job', 'about company', 'company info', 'address', 'role:', 'job title:', 'minimum qualifications', 'preferred qualifications']
                if any(pattern in line.lower() for pattern in skip_patterns):
                    continue
                if '@' not in line and 'http' not in line and not line.startswith('₹') and not line.startswith('$') and not line.isdigit():
                    if any(keyword in line.lower() for keyword in ['ltd', 'inc', 'corp', 'llc', 'technologies', 'solutions', 'systems', 'smart', 'ai', 'tech', 'software', 'pvt']):
                        company_counts[line] = company_counts.get(line, 0) + 1

        if company_counts:
            most_common = max(company_counts.items(), key=lambda x: x[1])
            if most_common[1] >= 2:
                return most_common[0]

        # Pattern 5: About [Company]
        about_match = re.search(r'About\s+([^\n\r]+)', text, re.IGNORECASE)
        if about_match:
            company = about_match.group(1).strip()
            if not any(word in company.lower() for word in ['the job', 'the company', 'the role', 'us']):
                return company

        # Pattern 6: Look for company-like patterns in first few lines
        for line in lines[:8]:
            line = line.strip()
            if not line:
                continue
            if any(line.lower().startswith(indicator) for indicator in ['job title', 'location', 'salary', 'about the job']):
                continue
            if any(keyword in line.lower() for keyword in ['ltd', 'inc', 'corp', 'llc', 'technologies', 'solutions', 'systems', 'smart', 'ai', 'tech']):
                return line

        if len(text) > 200:
            return "Unknown Company"

        return self._extract_company(lines)
    
    def _extract_domain(self, lines):
        """Extract company domain from text"""
        import re
        for line in lines:
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', line)
            if emails:
                domain = emails[0].split('@')[1]
                return domain
        return ""
    
    def _extract_location(self, lines):
        """Extract location from text"""
        import re

        # Pattern 1: Explicit location/city field
        for line in lines:
            if 'location' in line.lower() or 'city' in line.lower():
                location = line.split(':')[-1].strip()
                if location and location != line.strip():
                    return location

        # Pattern 2: Look for city names
        cities = ['Mumbai', 'Delhi', 'Bangalore', 'Bengaluru', 'Chennai', 'Hyderabad', 'Pune', 'Kolkata', 'Ahmedabad', 'Jaipur', 'Surat', 'Lucknow', 'Kanpur', 'Nagpur', 'Indore', 'Thane', 'Bhopal', 'Visakhapatnam', 'Patna', 'Vadodara', 'Ghaziabad', 'Ludhiana', 'Agra', 'Nashik', 'Faridabad', 'Meerut', 'Rajkot', 'Kalyan', 'Vasai', 'Varanasi', 'Srinagar', 'Aurangabad', 'Dhanbad', 'Amritsar', 'Navi Mumbai', 'Allahabad', 'Howrah', 'Ranchi', 'Gwalior', 'Jabalpur', 'Coimbatore', 'Vijayawada', 'Jodhpur', 'Madurai', 'Raipur', 'Kota', 'Guwahati', 'Chandigarh', 'Solapur', 'Hubli', 'Bareilly', 'Moradabad', 'Mysore', 'Gurgaon', 'Gurugram', 'Noida', 'Greater Noida']

        for line in lines[:10]:
            line = line.strip()
            if line:
                for city in cities:
                    if line.lower() == city.lower():
                        return city
                    if city.lower() in line.lower():
                        if re.search(r'\b' + re.escape(city) + r'\b', line, re.IGNORECASE):
                            return city

        # Pattern 3: Look for location patterns
        for line in lines[:15]:
            line = line.strip()
            if not line:
                continue
            skip_indicators = ['company', 'duration', 'month', 'remote', 'hiring office', 'applied', 'internship', 'description', 'key responsibilities', 'skill', 'preferred candidate', 'industry type', 'department', 'employment type', 'education', 'key skills', 'report this job', 'about company', 'company info', 'address', 'role:', 'job title:', 'minimum qualifications', 'preferred qualifications', 'responsibilities include', 'you will', 'what you will do', 'send me roles', 'company logo']
            if any(indicator in line.lower() for indicator in skip_indicators):
                continue
            if len(line) < 30 and not line.startswith('₹') and not line.startswith('$') and not '@' in line:
                if any(state in line.lower() for state in ['maharashtra', 'karnataka', 'tamil nadu', 'telangana', 'gujarat', 'rajasthan', 'uttar pradesh', 'madhya pradesh', 'west bengal', 'punjab', 'haryana', 'india']):
                    return line
                if ',' in line or line.isupper() or len(line.split()) <= 3:
                    return line

        return "Not Specified"
    
    def _extract_requirements(self, lines):
        """Extract requirements from text"""
        requirements = []
        capture = False
        
        for line in lines:
            if 'requirement' in line.lower() or 'skill' in line.lower():
                capture = True
                continue
            
            if capture and line.strip():
                if any(keyword in line.lower() for keyword in ['salary', 'location', 'apply']):
                    break
                requirements.append(line.strip())
        
        return ' '.join(requirements)
    
    def _extract_salary(self, lines):
        """Extract salary information from text"""
        import re
        for line in lines:
            if 'salary' in line.lower() or '$' in line or '₹' in line:
                salary_match = re.search(r'[\$₹]\s*[\d,]+', line)
                if salary_match:
                    return salary_match.group()
                return line.split(':')[-1].strip()
        return "Not Specified"
    
    def _analyze_job_data(self, job_data):
        """Analyze job data with AI model and enhanced red flag detection"""

        # Extract features
        features, combined_text = self.feature_extractor.extract_all_features(job_data)

        # Use enhanced red flag detection
        description = job_data.get('description', '')
        requirements = job_data.get('requirements', '')
        salary = job_data.get('salary', '')

        # Get comprehensive red flags
        red_flags_score, red_flags_dict = count_red_flags(description)

        # Convert red flags dict
        red_flags = []
        for flag_name, weight in red_flags_dict.items():
            if weight > 0:
                red_flags.append(flag_name)

        # Update features with red flags
        features['red_flag_count'] = len(red_flags)
        features['red_flags'] = red_flags
        features['red_flags_score'] = red_flags_score

        # Enhanced rule-based scoring
        combined_score = self._fast_prediction(features, red_flags)

        # Determine final prediction
        final_prediction = "FAKE JOB" if combined_score > 0.5 else "GENUINE JOB"

        # Calculate red flags severity
        red_flags_severity = self._assess_severity(red_flags, combined_score)

        # Domain analysis
        domain = job_data.get('company_domain', '')
        if domain:
            try:
                domain_analysis = analyze_domain_complete(domain + " " + job_data.get('description', ''))
                result['domain_analysis'] = domain_analysis
            except Exception as e:
                pass

        # Create result
        result = {
            'final_prediction': final_prediction,
            'is_fake': combined_score > 0.5,
            'ai_confidence': float(combined_score) * 100,
            'combined_confidence': float(combined_score) * 100,
            'red_flags_count': len(red_flags),
            'red_flags_list': red_flags,
            'red_flags_severity': red_flags_severity,
            'job_portal': job_data.get('job_portal', 'Unknown'),
            'company': job_data.get('company', 'Unknown'),
            'company_domain': job_data.get('company_domain', ''),
            'job_title': job_data.get('title', 'Unknown'),
            'location': job_data.get('location', 'Not Specified'),
            'description_preview': self._create_description_preview(job_data.get('description', '')),
            'url': job_data.get('url', ''),
            'success': True,
            'error': None
        }

        return result, features
    
    def _combine_predictions(self, ai_score, features, red_flags):
        """Combine AI prediction with rule-based scoring"""
        
        # Start with AI score (60% weight)
        combined = ai_score * 0.6
        
        # Add rule-based score (40% weight)
        rule_score = 0.0
        
        # More red flags = higher fake score
        red_flag_weight = min(len(red_flags) * 0.1, 1.0)
        rule_score += red_flag_weight * 0.5
        
        # Suspicious domain indicator
        if features.get('has_suspicious_domain'):
            rule_score += 0.3
        
        # Grammar/spelling errors indicator
        if features.get('spelling_errors', 0) > 5:
            rule_score += 0.2
        
        # Low unique word ratio (copied content)
        if features.get('unique_word_ratio', 1.0) < 0.3:
            rule_score += 0.2
        
        combined += rule_score * 0.4
        
        return min(combined, 1.0)

    def _fast_prediction(self, features, red_flags):
        """Enhanced rule-based prediction using advanced features"""
        score = 0.05

        # Use the red flag score from enhanced detection as primary indicator
        red_flag_score = features.get('red_flags_score', 0)
        if red_flag_score > 0:
            normalized_red_score = min(red_flag_score / 20.0, 1.0)
            score += normalized_red_score * 0.6
        else:
            score -= 0.1

        # Additional red flag analysis
        if red_flags:
            critical_patterns = ['registration fee', 'pay fee', 'payment required', 'upfront payment',
                               'bitcoin', 'cryptocurrency', 'blockchain investment', 'crypto investment',
                               'guaranteed income', 'guaranteed job', 'no interview', 'no background check',
                               'fake degree accepted', 'illegal work']
            critical_count = sum(1 for flag in red_flags if any(pattern in flag.lower() for pattern in critical_patterns))

            high_risk_patterns = ['urgent hiring', 'whatsapp', 'telegram', 'viber', 'skype',
                                'work from home guaranteed', 'no experience needed', 'easy money',
                                'get rich quick', 'passive income', 'micro task', 'captcha entry']
            high_risk_count = sum(1 for flag in red_flags if any(pattern in flag.lower() for pattern in high_risk_patterns))

            other_flags = len(red_flags) - critical_count - high_risk_count

            score += critical_count * 0.15
            score += high_risk_count * 0.08
            score += other_flags * 0.03

        # Enhanced domain analysis
        suspicious_domain_score = features.get('has_suspicious_domain', 0)
        if suspicious_domain_score > 0:
            score += suspicious_domain_score * 0.2

        # Text quality indicators - IMPROVED
        text_quality = features.get('text_quality_score', 0.5)
        text_length = features.get('text_length', 0)
        
        # Good text quality and adequate length = more legitimate
        if text_quality > 0.6 and text_length > 500:
            score -= 0.15  # Boost genuine jobs
        elif text_quality < 0.3:
            score += 0.1
        elif text_quality > 0.7:
            score -= 0.05

        # Sentiment analysis - check for overly positive (suspicious) content
        sentiment_polarity = features.get('sentiment_polarity', 0)
        if sentiment_polarity > 0.7:  # Too positive might be fake
            score += 0.08
        elif sentiment_polarity > 0.5:
            score += 0.03

        # Readability - very poor or very good can indicate issues
        readability = features.get('readability_score', 0.5)
        if readability < 0.2 or readability > 0.9:
            score += 0.03

        # Professional term ratio - important indicator
        prof_ratio = features.get('professional_term_ratio', 0)
        if prof_ratio < 0.05:
            score += 0.08
        elif prof_ratio > 0.2:
            score -= 0.1  # More professional = more legitimate

        # Lexical diversity
        lexical_div = features.get('lexical_diversity', 0.5)
        if lexical_div < 0.3:
            score += 0.06  # Low diversity might indicate copy-paste

        # Suspicion score
        suspicion_score = features.get('suspicion_score', 0)
        score += suspicion_score * 0.3

        # Red flag combination score
        combo_score = features.get('red_flag_combo_score', 0)
        score += combo_score * 0.2

        # POSITIVE INDICATORS (reduce fake score) - IMPROVED
        positive_score = 0
        
        # Has company domain (verified company)
        if features.get('domain_exists') and suspicious_domain_score == 0:
            positive_score += 0.15
        
        # Adequate text length (real jobs have detailed descriptions)
        if text_length > 600:
            positive_score += 0.08
        elif text_length > 1000:
            positive_score += 0.12
        
        # Good professional term ratio
        if prof_ratio > 0.15:
            positive_score += 0.1
        
        # Good readability (not too simple, not too complex)
        if 0.4 <= readability <= 0.7:
            positive_score += 0.05
        
        # Good lexical diversity (varied vocabulary)
        if lexical_div > 0.5:
            positive_score += 0.05
        
        # No red flags at all
        if red_flag_score == 0 and len(red_flags) == 0:
            positive_score += 0.15
        
        # Apply positive score
        score -= positive_score

        return max(0, min(score, 1.0))
    
    def _assess_severity(self, red_flags, combined_score):
        """Assess severity level of red flags"""
        
        critical_flags = ['suspicious_email', 'spam_phrase', 'unrealistic_salary']
        critical_count = sum(1 for flag in red_flags if flag in critical_flags)
        
        if critical_count > 0 or combined_score > 0.8:
            return "High"
        elif len(red_flags) > 3 or combined_score > 0.6:
            return "Medium"
        else:
            return "Low"
    
    def _assess_job_quality(self, analysis_result, features=None):
        """Enhanced job quality assessment"""

        confidence = analysis_result['combined_confidence']
        red_flags = analysis_result['red_flags_count']
        is_fake = analysis_result['is_fake']

        quality_score = 50

        if red_flags == 0:
            quality_score += 35
        elif red_flags == 1:
            quality_score += 20
        elif red_flags == 2:
            quality_score += 10
        elif red_flags == 3:
            quality_score += 0
        elif red_flags <= 5:
            quality_score -= 10
        else:
            quality_score -= red_flags * 8

        if confidence >= 90:
            quality_score += 25
        elif confidence >= 80:
            quality_score += 20
        elif confidence >= 70:
            quality_score += 15
        elif confidence >= 60:
            quality_score += 10
        elif confidence >= 50:
            quality_score += 5
        elif confidence >= 40:
            quality_score += 0
        elif confidence >= 30:
            quality_score -= 5
        elif confidence >= 20:
            quality_score -= 10
        else:
            quality_score -= 20

        if features:
            text_quality = features.get('text_quality_score', 0.5)
            quality_score += (text_quality - 0.5) * 50

            prof_ratio = features.get('professional_term_ratio', 0)
            if prof_ratio > 0.2:
                quality_score += 25
            elif prof_ratio > 0.15:
                quality_score += 20
            elif prof_ratio > 0.1:
                quality_score += 15
            elif prof_ratio > 0.05:
                quality_score += 10
            else:
                quality_score -= 15

            readability = features.get('readability_score', 0.5)
            if 0.4 <= readability <= 0.7:
                quality_score += 15
            elif 0.3 <= readability <= 0.8:
                quality_score += 10
            elif readability < 0.2 or readability > 0.9:
                quality_score -= 10

            lexical_div = features.get('lexical_diversity', 0.5)
            if lexical_div > 0.7:
                quality_score += 10
            elif lexical_div > 0.6:
                quality_score += 8
            elif lexical_div > 0.5:
                quality_score += 5
            elif lexical_div < 0.3:
                quality_score -= 15
            elif lexical_div < 0.4:
                quality_score -= 10

            domain_score = 0
            if features.get('domain_exists'):
                domain_score += 20
                if features.get('has_suspicious_domain', 0) < 0.3:
                    domain_score += 10
            elif features.get('has_suspicious_domain', 0) > 0.7:
                domain_score -= 30
            elif features.get('has_suspicious_domain', 0) > 0.5:
                domain_score -= 20
            else:
                domain_score -= 10

            quality_score += domain_score

            sentiment_polarity = features.get('sentiment_polarity', 0)
            if abs(sentiment_polarity) < 0.2:
                quality_score += 8
            elif abs(sentiment_polarity) < 0.4:
                quality_score += 5
            elif sentiment_polarity > 0.7:
                quality_score -= 10
            elif sentiment_polarity < -0.3:
                quality_score -= 5

            text_length = features.get('text_length', 0)
            if text_length > 800:
                quality_score += 10
            elif text_length > 500:
                quality_score += 5
            elif text_length < 200:
                quality_score -= 15
            elif text_length < 300:
                quality_score -= 10

            sentence_complexity = features.get('sentence_complexity', 0)
            if 0.5 <= sentence_complexity <= 1.5:
                quality_score += 5
            elif sentence_complexity > 2.0:
                quality_score -= 5

        if is_fake:
            if confidence > 80:
                quality_score = max(5, quality_score * 0.3)
            elif confidence > 60:
                quality_score = max(10, quality_score * 0.4)
            else:
                quality_score = max(15, quality_score * 0.5)

        quality_score = max(0, min(100, quality_score))

        if quality_score >= 90:
            return "EXCELLENT"
        elif quality_score >= 80:
            return "VERY HIGH"
        elif quality_score >= 70:
            return "HIGH"
        elif quality_score >= 60:
            return "GOOD"
        elif quality_score >= 50:
            return "MODERATE"
        elif quality_score >= 40:
            return "FAIR"
        elif quality_score >= 30:
            return "LOW"
        elif quality_score >= 20:
            return "VERY LOW"
        elif quality_score >= 10:
            return "POOR"
        else:
            return "SUSPICIOUS"
    
    def _detect_job_portal(self, text):
        """Detect job portal from URL patterns or text content"""
        text_lower = text.lower()

        # Check for URL patterns
        if 'naukri.com' in text_lower:
            return 'naukri.com'
        elif 'linkedin.com' in text_lower:
            return 'linkedin.com'
        elif 'indeed.com' in text_lower:
            return 'indeed.com'
        elif 'internshala.com' in text_lower:
            return 'internshala.com'

        # Check for platform-specific content patterns
        if 'send me roles like this' in text_lower:
            return 'naukri.com'
        elif 'apply on company site' in text_lower and 'linkedin' in text_lower:
            return 'linkedin.com'
        elif 'report this job' in text_lower:
            return 'naukri.com'

        return 'manual_input'

    def _create_description_preview(self, description, max_length=500):
        """Create a preview of the job description"""
        if not description:
            return "No description available"

        description = description.strip()

        if len(description) > max_length:
            description = description[:max_length] + "..."

        return description
