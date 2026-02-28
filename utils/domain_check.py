import re
from urllib.parse import urlparse
import socket
import whois
from datetime import datetime

def get_company_domain(text):
    """Extract company domain from text or URL"""
    # If URL pasted
    if text.startswith("http"):
        parsed = urlparse(text)
        return parsed.scheme + "://" + parsed.netloc

    # Try to extract company website from text
    urls = re.findall(r"https?://\S+", text)
    if urls:
        parsed = urlparse(urls[0])
        return parsed.scheme + "://" + parsed.netloc

    return "Not available"


def extract_domain_from_url(url):
    """Extract clean domain from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return None


def is_suspicious_domain(domain):
    """Enhanced suspicious domain pattern detection"""
    if not domain or domain == "Not available":
        return True, "No valid domain found"
    
    # Check for suspicious TLDs
    suspicious_tlds = ['.xyz', '.top', '.work', '.click', '.link', '.club', 
                      '.date', '.racing', '.science', '.gq', '.ml', '.tk',
                      '.cf', '.ga', '.buzz', '.info']
    
    for tld in suspicious_tlds:
        if domain.endswith(tld):
            return True, f"Suspicious TLD: {tld}"
    
    # Check for excessive subdomains
    parts = domain.split('.')
    if len(parts) > 4:
        return True, "Excessive subdomains"
    
    # Check for numbers in domain (common in scam domains)
    if any(c.isdigit() for c in domain.split('.')[-2]):
        # Allow legitimate domains with numbers (like yahoo.co.in)
        if not re.match(r'^[a-zA-Z0-9]+\.[a-zA-Z]{2,}$', domain.split('.')[-2] + '.' + domain.split('.')[-1]):
            return True, "Suspicious number pattern in domain"
    
    # Check for hyphens pattern (common in fake domains)
    if domain.count('-') > 2:
        return True, "Multiple hyphens in domain"
    
    # Check for lookalike domains (common substitutions)
    lookalikes = {
        'gooogle': 'google',
        'googel': 'google',
        'amaz0n': 'amazon',
        'microsft': 'microsoft',
        'micros0ft': 'microsoft',
        'appple': 'apple',
        'faceb00k': 'facebook',
        'linkdin': 'linkedin',
        'linkedln': 'linkedin'
    }
    
    domain_lower = domain.lower()
    for fake, real in lookalikes.items():
        if fake in domain_lower:
            return True, f"Possible lookalike domain (fake {fake}, real {real})"
    
    return False, "Domain appears legitimate"


def get_domain_age(domain):
    """Get domain age and creation date"""
    try:
        if not domain or domain == "Not available":
            return None
        
        w = whois.whois(domain)
        if w.creation_date:
            if isinstance(w.creation_date, list):
                creation_date = w.creation_date[0]
            else:
                creation_date = w.creation_date
            
            if isinstance(creation_date, str):
                # Try to parse string date
                try:
                    creation_date = datetime.strptime(creation_date.split(' ')[0], '%Y-%m-%d')
                except:
                    return None
            
            age_days = (datetime.now() - creation_date).days
            return {
                'age_days': age_days,
                'age_years': age_days / 365,
                'creation_date': creation_date.strftime('%Y-%m-%d') if hasattr(creation_date, 'strftime') else str(creation_date)
            }
    except:
        pass
    
    return None


def check_domain_reputation(domain):
    """Check domain reputation based on age and patterns"""
    age_info = get_domain_age(domain)
    
    if not age_info:
        return {
            'reputation_score': 50,
            'trust_level': 'UNKNOWN',
            'reason': 'Could not verify domain age'
        }
    
    age_days = age_info['age_days']
    
    # Domain age scoring
    if age_days < 30:
        reputation_score = 20
        trust_level = 'VERY_LOW'
        reason = 'Domain created less than 30 days ago'
    elif age_days < 90:
        reputation_score = 40
        trust_level = 'LOW'
        reason = 'Domain less than 3 months old'
    elif age_days < 180:
        reputation_score = 60
        trust_level = 'MEDIUM'
        reason = 'Domain less than 6 months old'
    elif age_days < 365:
        reputation_score = 75
        trust_level = 'GOOD'
        reason = 'Domain less than 1 year old'
    else:
        reputation_score = 90
        trust_level = 'HIGH'
        reason = f'Domain is {age_days // 365} years old'
    
    return {
        'reputation_score': reputation_score,
        'trust_level': trust_level,
        'reason': reason,
        'age_info': age_info
    }


def verify_company_legitimacy(company_name, domain):
    """Enhanced company legitimacy verification"""
    legitimacy_indicators = []
    score = 50  # Base score
    
    # Check if domain matches company name
    if company_name and domain and domain != "Not available":
        company_lower = company_name.lower().replace(' ', '')
        domain_lower = domain.lower().replace('www.', '').replace('https://', '').replace('http://', '').split('.')[0]
        
        # Check for partial match
        if company_lower in domain_lower or domain_lower in company_lower:
            score += 20
            legitimacy_indicators.append("Company name matches domain")
        else:
            # Check for common words
            common_words = ['inc', 'corp', 'llc', 'ltd', 'co', 'company', 'group', 'solutions', 'tech', 'systems']
            if any(word in company_lower for word in common_words):
                score += 10
                legitimacy_indicators.append("Company name contains common business words")
    
    # Check domain reputation
    if domain and domain != "Not available":
        reputation = check_domain_reputation(domain)
        score += (reputation['reputation_score'] - 50)  # Adjust based on reputation
        
        if reputation['trust_level'] in ['HIGH', 'GOOD']:
            legitimacy_indicators.append(f"Domain trust level: {reputation['trust_level']}")
        elif reputation['trust_level'] in ['VERY_LOW', 'LOW']:
            legitimacy_indicators.append(f"Warning: {reputation['reason']}")
    
    # Cap score between 0-100
    score = max(0, min(100, score))
    
    # Determine legitimacy level
    if score >= 80:
        legitimacy_level = 'VERIFIED'
    elif score >= 60:
        legitimacy_level = 'LIKELY_LEGITIMATE'
    elif score >= 40:
        legitimacy_level = 'UNCERTAIN'
    elif score >= 20:
        legitimacy_level = 'SUSPICIOUS'
    else:
        legitimacy_level = 'LIKELY_FAKE'
    
    return {
        'score': score,
        'legitimacy_level': legitimacy_level,
        'indicators': legitimacy_indicators,
        'domain': domain,
        'company': company_name
    }


def analyze_domain_complete(text):
    """Complete domain analysis with all metrics"""
    # Extract domain
    domain = get_company_domain(text)
    
    # Check for suspicious patterns
    is_suspicious, suspicion_reason = is_suspicious_domain(domain)
    
    # Get reputation
    reputation = check_domain_reputation(domain)
    
    # Extract company name if possible
    company_match = re.search(r'(?:company|organization|company name)[:\s]+([A-Za-z0-9\s]+?)(?:\n|$)', text, re.IGNORECASE)
    company_name = company_match.group(1).strip() if company_match else None
    
    # Verify legitimacy
    legitimacy = verify_company_legitimacy(company_name, domain)
    
    return {
        'domain': domain,
        'is_suspicious': is_suspicious,
        'suspicion_reason': suspicion_reason,
        'reputation': reputation,
        'legitimacy': legitimacy
    }
