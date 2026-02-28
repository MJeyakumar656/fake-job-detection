import re
from collections import defaultdict

def count_red_flags(text):
    """Enhanced red flag detection with improved accuracy and context awareness"""
    text_lower = text.lower()
    text_clean = re.sub(r'[^\w\s]', ' ', text_lower)  # Remove punctuation for better matching

    # Initialize scoring system
    total_score = 0
    found_flags = defaultdict(int)
    context_multipliers = []

    # Critical Red Flags (Weight: 4) - Strongest indicators of scams
    critical_flags = {
        "registration fee": 4,
        "pay fee": 4,
        "payment required": 4,
        "upfront payment": 4,
        "processing fee": 4,
        "application fee": 4,
        "training fee": 4,
        "deposit required": 4,
        "money transfer": 4,
        "western union": 4,
        "wire transfer": 4,
        "bitcoin": 4,
        "cryptocurrency": 4,
        "blockchain investment": 4,
        "crypto investment": 4,
        "guaranteed income": 4,
        "guaranteed job": 4,
        "earn $": 4,
        "earn ₹": 4,
        "make money fast": 4,
        "easy money": 4,
        "get rich quick": 4,
        "no interview": 4,
        "no interview process": 4,
        "no assessment": 4,
        "skip interview": 4,
        "instant hire": 4,
        "instant approval": 4,
        "no verification": 4,
        "no background check": 4,
        "no experience needed": 4,
        "no qualification needed": 4,
        "no degree required": 4,
        "fake degree accepted": 4,
        "forged documents": 4,
        "illegal work": 4,
        "underground job": 4,
        "black market": 4,
    }
    
    # High Risk Flags (Weight: 3) - Strong indicators with context awareness
    high_risk_flags = {
        "work from home guaranteed": 3,
        "urgent hiring": 3,
        "urgent recruitment": 3,
        "limited time offer": 3,
        "limited positions": 3,
        "act now": 3,
        "don't miss": 3,
        "don't delay": 3,
        "hurry up": 3,
        "apply immediately": 3,
        "apply asap": 3,
        "freshers welcome": 3,
        "guaranteed placement": 3,
        "100% job guarantee": 3,
        "click here": 3,
        "click link": 3,
        "copy paste": 3,
        "copy-paste": 3,
        "home based": 3,
        "part time": 3,
        "passive income": 3,
        "side hustle": 3,
        "extra income": 3,
        "earn while you": 3,
        "earn from home": 3,
        "work from anywhere": 3,
        "flexible hours": 3,
        "own boss": 3,
        "be your own boss": 3,
        "whatsapp": 3,
        "telegram": 3,
        "viber": 3,
        "skype": 3,
        "contact via whatsapp": 3,
        "contact via telegram": 3,
        "dm only": 3,
        "dm for details": 3,
        "message for details": 3,
        "inbox for details": 3,
        "typing work": 3,
        "online typing": 3,
        "form filling": 3,
        "captcha entry": 3,
        "micro task": 3,
        "crowdsource": 3,
        "freelance platform": 3,
        "upwork alternative": 3,
        "fiverr competitor": 3,
    }
    
    # Medium Risk Flags (Weight: 1) - Moderate indicators
    medium_risk_flags = {
        "no interview required": 1,
        "phone interview only": 1,
        "online interview": 1,
        "no office visit": 1,
        "remote only": 1,
        "work anywhere": 1,
        "multilevel marketing": 1,
        "mlm": 1,
        "network marketing": 1,
        "pyramid scheme": 1,
        "referral bonus": 1,
        "referral commission": 1,
        "recruitment bonus": 1,
        "refer friends": 1,
        "refer and earn": 1,
        "get commission": 1,
        "commission only": 1,
        "no salary": 1,
        "performance based": 1,
        "variable pay": 1,
        "bonus heavy": 1,
        "incentive based": 1,
        "data entry": 1,
        "typing job": 1,
        "transcription": 1,
        "surveys": 1,
        "online jobs": 1,
        "internet job": 1,
        "online work": 1,
        "part time online": 1,
        "freelance": 1,
        "contract": 1,
        "temporary": 1,
        "gig": 1,
        "gig economy": 1,
    }
    
    # Enhanced Red Flag Patterns with better regex and higher accuracy
    pattern_flags = [
        # Financial red flags - highest priority
        (r'\$\s*\d{4,6}\s*(?:per|daily|weekly|monthly|guaranteed|hour)', 3, "Unrealistic high income promise"),
        (r'₹\s*\d{5,7}\s*(?:per|daily|weekly|monthly|guaranteed|hour)', 3, "Unrealistic high income promise"),
        (r'(?:earn|make|get|receive)\s+\$?\d{4,}\s*(?:per|daily|weekly|guaranteed)', 3, "Unrealistic earnings claim"),
        (r'(?:earn|make|get|receive)\s+₹\d{5,}\s*(?:per|daily|weekly|guaranteed)', 3, "Unrealistic earnings claim"),
        (r'(?:salary|pay|income|compensation)\s*(?:of|is|:)\s*\$?\d{4,}', 2, "Suspicious salary mention"),
        (r'(?:salary|pay|income|compensation)\s*(?:of|is|:)\s*₹\d{5,}', 2, "Suspicious salary mention"),

        # Work pattern red flags - More specific to avoid legitimate remote work
        (r'(?:work|job)\s+\d+\s*(?:hour|hrs|hour per|hours per)\s*(?:day|week|month)', 2, "Suspicious work schedule"),
        (r'(?:only|just|mere)\s*\d+\s*(?:hour|hrs)\s+(?:per|daily|day)', 2, "Unrealistic work hours"),
        # Only flag unprofessional locations when combined with scam indicators
        (r'(?:work\s+)?(?:from|in)\s+(?:car|coffee|cafe|bed|anywhere)\s*(?:and|or|with)?\s*(?:no|without)\s*(?:supervision|boss|manager)', 3, "Unprofessional work location"),
        (r'(?:work\s+)?(?:from|in)\s+(?:car|coffee|cafe|bed|anywhere)\s+(?:only|exclusively|strictly)', 2, "Unprofessional work location"),

        # Contact method red flags - More specific to avoid platform UI elements
        (r'(?:call|contact|reach|whatsapp|text|message)\s+(?:us|me|this number|\+?\d{10,})', 2, "Direct contact emphasis"),
        (r'(?:only|strictly|exclusively)\s+(?:whatsapp|telegram|call|text|phone)', 3, "Non-standard contact method"),
        # Exclude common platform UI elements like "Send me roles like this"
        (r'(?:send|text|message|dm|inbox)\s+(?:me|us|this number)(?!\s+(?:roles|jobs|updates|notifications))', 2, "Personal contact request"),
        (r'(?:whatsapp|telegram|skype|viber)\s+(?:only|required|mandatory)', 3, "Communication restriction"),

        # Urgency and pressure tactics
        (r'(?:must|immediately|urgently|asap|now)\s+(?:join|start|begin|apply)', 2, "Pressure to join quickly"),
        (r'(?:only|limited|few)\s+\d+\s+(?:position|seat|spot|vacancy|opening)', 2, "Artificial scarcity"),
        (r'(?:last|final|ending)\s+(?:chance|opportunity|date)', 2, "Deadline pressure"),
        (r'(?:don\'?t\s+(?:miss|delay|wait)|hurry\s+up|act\s+now)', 2, "Urgency language"),

        # Verification and process red flags
        (r'(?:no|not|without|skip)\s+(?:background check|verification|interview|assessment)', 3, "Skipping verification"),
        (r'(?:fake|forged|photocopy)\s+(?:documents?|certificates?|degrees?)', 4, "Document fraud acceptance"),
        (r'(?:any|no|fake)\s+(?:degree|qualification|experience)\s+(?:accepted|required)', 3, "Fake credentials acceptance"),

        # Discriminatory and illegal content
        (r'(?:requirement|requirement|only|prefer)[:.]?\s*(?:age|gender|caste|religion|marital)', 3, "Discriminatory posting"),
        (r'(?:male|female|boy|girl)\s+(?:only|preferred|required)', 3, "Gender discrimination"),
        (r'(?:illegal|underground|black market|grey market)', 4, "Illegal work mention"),

        # Investment and payment red flags
        (r'(?:investment|deposit|fee|payment)\s+(?:required|needed|mandatory)', 4, "Investment required"),
        (r'(?:refundable|returnable|guaranteed return)', 3, "Investment promise"),
        (r'(?:bitcoin|crypto|blockchain)\s+(?:investment|required|needed)', 4, "Crypto investment scheme"),

        # MLM and pyramid scheme indicators
        (r'(?:mlm|multi.?level.?marketing|pyramid|network.?marketing)', 3, "MLM/pyramid scheme"),
        (r'(?:referral|commission|bonus)\s+(?:based|heavy|only)', 2, "Commission-based structure"),
        (r'(?:recruit|refer)\s+(?:friends|family|people)', 2, "Recruitment focus"),

        # Scam-specific phrases
        (r'(?:get rich quick|easy money|passive income|residual income)', 3, "Get rich quick scheme"),
        (r'(?:work from home|remote work)\s+(?:guaranteed|assured)', 3, "Guaranteed remote work"),
        (r'(?:no experience|no skills|no qualification)\s+(?:needed|required)', 3, "No requirements claim"),

        # Professionalism indicators (negative when missing)
        (r'(?:about\s+(?:us|the\s+company)|company\s+profile|our\s+mission)', 0, "Company information present"),
        (r'(?:responsibilities|requirements|qualifications|skills)', 0, "Job details present"),
        (r'(?:benefits|salary|compensation|perks)', 0, "Compensation details present"),

        # NEW: Emerging scam patterns - AI/ML and tech scams
        (r'(?:ai|artificial intelligence|machine learning|ml|deep learning)\s+(?:job|work|opportunity)\s+(?:guaranteed|assured)', 3, "AI/ML scam promise"),
        (r'(?:ai|ml|data science)\s+(?:certification|course|training)\s+(?:free|paid|investment)', 2, "AI training scam"),
        (r'(?:blockchain|crypto|web3|nft)\s+(?:developer|engineer|specialist)\s+(?:remote|home)', 3, "Crypto job scam"),
        (r'(?:metaverse|vr|ar|virtual reality)\s+(?:job|career|opportunity)', 2, "Metaverse job scam"),

        # NEW: Modern remote work scams
        (r'(?:remote|home|flexible)\s+(?:work|job)\s+(?:unlimited|unrestricted|freedom)', 3, "Fake remote work freedom"),
        (r'(?:set\s+your\s+own\s+(?:hours|schedule|pace)|work\s+when\s+you\s+want)', 2, "Unrealistic flexibility"),
        (r'(?:no\s+(?:boss|manager|supervisor|office)|own\s+(?:boss|schedule))', 3, "No supervision claim"),

        # NEW: Unrealistic tech promises
        (r'(?:learn\s+(?:coding|programming|development)\s+in\s+\d+\s+(?:days?|weeks?|months?))', 3, "Impossible learning timeline"),
        (r'(?:become\s+(?:developer|engineer|expert)\s+in\s+\d+\s+(?:days?|weeks?|months?))', 3, "Unrealistic career promise"),
        (r'(?:guaranteed\s+(?:placement|job|career)\s+(?:after|upon)\s+(?:completion|course|training))', 3, "Guaranteed placement scam"),

        # NEW: Advanced scam tactics
        (r'(?:copy\s+paste|copy-paste|ctrl\+c|ctrl\+v)\s+(?:work|job|tasks?)', 3, "Copy-paste job scam"),
        (r'(?:micro\s+tasks?|nano\s+tasks?|click\s+work|captcha\s+entry)', 3, "Micro-task exploitation"),
        (r'(?:crowdfunding|crowdsource|platform\s+(?:like|similar\s+to)\s+(?:upwork|fiverr))', 2, "Fake freelancing platform"),

        # NEW: Investment-based job scams
        (r'(?:invest\s+(?:small|little|minimal)\s+amount|initial\s+investment)', 4, "Investment-based job"),
        (r'(?:roi|return\s+on\s+investment|profit\s+sharing|revenue\s+sharing)', 3, "Investment return promise"),
        (r'(?:partnership|joint\s+venture|business\s+opportunity)', 2, "Business partnership scam"),

        # NEW: Psychological manipulation
        (r'(?:limited\s+spots?|exclusive\s+opportunity|vip\s+access)', 2, "Exclusivity manipulation"),
        (r'(?:don\'?t\s+tell\s+(?:anyone|others)|keep\s+it\s+(?:secret|confidential))', 3, "Secrecy requirement"),
        (r'(?:only\s+(?:serious|candidates|qualified)\s+(?:need|apply))', 2, "Selective candidate claim"),

        # NEW: Fake company indicators
        (r'(?:startup|new\s+company|emerging\s+(?:company|business))\s+(?:with\s+)?(?:unlimited\s+potential|high\s+growth)', 2, "Fake startup promise"),
        (r'(?:revolutionary|disruptive|game.?changing)\s+(?:technology|platform|solution)', 2, "Overhyped technology"),
        (r'(?:backed\s+by|funded\s+by|invested\s+in\s+by)\s+(?:famous|celebrity|influencer)', 2, "Celebrity endorsement scam"),
    ]
    
    total_score = 0
    found_flags = []
    
    # Check critical flags
    for flag, weight in critical_flags.items():
        if flag in text_lower:
            total_score += weight
            found_flags.append((flag, weight))
    
    # Check high risk flags
    for flag, weight in high_risk_flags.items():
        if flag in text_lower:
            total_score += weight
            found_flags.append((flag, weight))
    
    # Check medium risk flags
    for flag, weight in medium_risk_flags.items():
        if flag in text_lower:
            total_score += weight
            found_flags.append((flag, weight))
    
    # Check pattern-based flags with context multipliers
    for pattern, weight, description in pattern_flags:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            # Apply context multipliers
            multiplier = 1.0
            if len(matches) > 1:
                multiplier = 1.5  # Multiple occurrences increase suspicion
            if any(word in text_clean for word in ['urgent', 'immediate', 'now', 'today']):
                multiplier *= 1.3  # Urgency words amplify red flags

            adjusted_weight = int(weight * multiplier)
            total_score += adjusted_weight
            found_flags.append((description, adjusted_weight))

    # Advanced heuristic checks with machine learning-inspired features

    # 1. Text quality analysis
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    if caps_ratio > 0.3:
        total_score += 2
        found_flags.append(("Excessive capitalization (SCAM indicator)", 2))
    elif caps_ratio > 0.5:
        total_score += 3
        found_flags.append(("ALL CAPS TEXT (Strong SCAM indicator)", 3))

    # 2. Enhanced spelling and grammar check - More lenient for legitimate jobs
    common_misspellings = [
        "heelo", "helo", "wel come", "succesful", "occassion", "recieve",
        "excelent", "seperete", "occured", "wiht", "adn", "teh", "reccommend",
        "experiance", "qualifed", "benifits", "salery", "comapny", "organiation"
    ]
    spelling_errors = 0
    for misspelling in common_misspellings:
        if misspelling in text_clean:
            spelling_errors += 1

    # Only flag if multiple spelling errors AND other scam indicators present
    if spelling_errors > 2:  # Reduced threshold
        weight = min(2, spelling_errors - 1)  # Reduced weight
        total_score += weight
        found_flags.append((f"Multiple spelling errors ({spelling_errors} found)", weight))
    elif spelling_errors == 1 and any(word in text_clean for word in ['urgent', 'guaranteed', 'easy money']):
        # Only flag single error if combined with scam words
        total_score += 1
        found_flags.append(("Minor spelling error with suspicious content", 1))

    # 3. Content structure analysis
    sentences = re.split(r'[.!?]+', text)
    avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

    # Very short sentences might indicate poor quality or scam
    if avg_sentence_length < 5 and len(sentences) > 10:
        total_score += 1
        found_flags.append(("Poor sentence structure", 1))

    # 4. Professional content check with weighted scoring
    professional_indicators = {
        'responsibilities': 0,
        'qualifications': 0,
        'requirements': 0,
        'skills': 0,
        'experience': 0,
        'education': 0,
        'benefits': 0,
        'salary': 0,
        'company': 0,
        'about us': 0,
        'contact': 0,
        'apply': 0
    }

    for indicator in professional_indicators:
        if indicator in text_lower:
            professional_indicators[indicator] = 1

    professional_score = sum(professional_indicators.values())

    # Penalize for missing professional content - More lenient for legitimate jobs
    # Only flag if very few professional indicators AND scam words present
    scam_context = any(word in text_clean for word in ['guaranteed', 'easy money', 'urgent', 'apply now', 'no experience'])

    if professional_score < 2 and scam_context:
        total_score += 2
        found_flags.append(("Missing professional job details", 2))
    elif professional_score < 3 and scam_context:
        total_score += 1
        found_flags.append(("Limited professional content", 1))
    # For legitimate jobs, don't penalize for missing some indicators

    # 5. Scam phrase density analysis
    scam_words = [
        'guaranteed', 'easy money', 'work from home', 'no experience', 'urgent',
        'apply now', 'limited time', 'investment', 'deposit', 'fee', 'bitcoin',
        'crypto', 'passive income', 'side hustle', 'extra income', 'commission'
    ]

    scam_word_count = sum(1 for word in scam_words if word in text_lower)
    total_words = len(text_clean.split())

    if total_words > 0:
        scam_density = scam_word_count / total_words
        if scam_density > 0.05:  # More than 5% scam words
            density_penalty = min(3, int(scam_density * 50))
            total_score += density_penalty
            found_flags.append((f"High scam phrase density ({scam_density:.1%})", density_penalty))

    # 6. Contact information analysis
    # Penalize for too many contact methods or unusual contact instructions
    contact_methods = ['whatsapp', 'telegram', 'phone', 'email', 'call', 'text', 'dm']
    contact_count = sum(1 for method in contact_methods if method in text_lower)

    if contact_count > 2:
        total_score += 1
        found_flags.append(("Multiple contact methods specified", 1))

    # 7. Money-related red flags with context
    money_indicators = ['$', '₹', 'dollar', 'rupee', 'salary', 'pay', 'earn', 'income']
    money_mentions = sum(1 for indicator in money_indicators if indicator in text_lower)

    if money_mentions > 3:
        total_score += 1
        found_flags.append(("Excessive money references", 1))

    # 8. Time pressure indicators
    urgency_words = ['urgent', 'immediate', 'asap', 'now', 'today', 'deadline', 'limited time', 'hurry']
    urgency_count = sum(1 for word in urgency_words if word in text_lower)

    if urgency_count > 2:
        urgency_penalty = min(2, urgency_count - 1)
        total_score += urgency_penalty
        found_flags.append(("High urgency pressure", urgency_penalty))
    
    # Remove duplicates but keep highest weight
    unique_flags = {}
    for flag, weight in found_flags:
        if flag not in unique_flags or unique_flags[flag] < weight:
            unique_flags[flag] = weight
    
    return total_score, unique_flags


def get_red_flag_details(text):
    """Get detailed red flag information"""
    score, flags = count_red_flags(text)
    return {
        "total_score": score,
        "flag_count": len(flags),
        "flags": flags,
        "severity": categorize_severity(score),
        "description": get_severity_description(score)
    }


def categorize_severity(score):
    """Categorize red flag severity"""
    if score >= 10:
        return "CRITICAL"
    elif score >= 6:
        return "HIGH"
    elif score >= 3:
        return "MEDIUM"
    elif score >= 1:
        return "LOW"
    else:
        return "NONE"


def get_severity_description(score):
    """Get description for severity level"""
    descriptions = {
        "CRITICAL": "🚨 This posting shows CRITICAL scam indicators. Do NOT apply!",
        "HIGH": "⚠️ This posting shows HIGH risk indicators. Proceed with extreme caution.",
        "MEDIUM": "⚡ This posting has MEDIUM risk indicators. Be cautious and verify information.",
        "LOW": "✓ This posting has LOW risk indicators. Generally looks legitimate.",
        "NONE": "✅ No major red flags detected. This posting appears legitimate."
    }
    return descriptions.get(categorize_severity(score), "Unknown")


def analyze_quality(text):
    """Analyze job posting quality based on multiple factors"""
    text_length = len(text)
    score, flags = count_red_flags(text)
    
    # Check for professional quality indicators
    quality_indicators = {
        'has_responsibilities': bool(re.search(r'responsibilit(?:y|ies)', text, re.IGNORECASE)),
        'has_qualifications': bool(re.search(r'qualifications?|requirements?|skills?', text, re.IGNORECASE)),
        'has_salary': bool(re.search(r'\$\s*\d+|₹\s*\d+|salary|compensation|ctc|package', text, re.IGNORECASE)),
        'has_company_info': bool(re.search(r'about\s+(?:us|the\s+company)|company|organization', text, re.IGNORECASE)),
        'has_location': bool(re.search(r'location|based|office|remote', text, re.IGNORECASE)),
        'has_benefits': bool(re.search(r'benefit|insurance|health|401k|pto|leave', text, re.IGNORECASE)),
        'proper_length': text_length > 300,
        'has_professional_format': text.count('\n') > 5,
    }
    
    quality_score = sum(1 for v in quality_indicators.values() if v)
    
    # Determine quality level
    if score >= 10:  # Critical red flags
        return "FAKE - SCAM"
    elif score >= 6:  # High risk
        return "SUSPICIOUS"
    elif score >= 3:  # Medium risk
        return "Questionable"
    elif quality_score >= 6:  # High quality indicators
        return "High"
    elif quality_score >= 4:  # Medium quality
        return "Medium"
    elif quality_score >= 2:  # Low quality
        return "Low"
    else:
        return "Very Low"


def get_quality_color(quality):
    """Get color coding for quality level"""
    colors = {
        "High": "#4caf50",      # Green
        "Medium": "#ff9800",    # Orange
        "Low": "#f44336",       # Red
        "Questionable": "#ff5722",  # Deep Orange
        "SUSPICIOUS": "#c62828",    # Dark Red
        "FAKE - SCAM": "#b71c1c",   # Very Dark Red
        "Very Low": "#f44336"   # Red
    }
    return colors.get(quality, "#999999")


def get_overall_assessment(text):
    """Get comprehensive assessment of job posting"""
    text_lower = text.lower()
    score, flags = count_red_flags(text)
    quality = analyze_quality(text)
    severity = categorize_severity(score)
    
    assessment = {
        "overall_quality": quality,
        "red_flag_score": score,
        "red_flag_count": len(flags),
        "severity_level": severity,
        "detected_flags": flags,
        "assessment_text": get_severity_description(score),
        "is_likely_scam": score >= 6,
        "is_high_risk": score >= 3,
        "confidence": min(100, score * 10) if score > 0 else 0,
    }
    
    return assessment
