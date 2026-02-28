import re

def clean_text(text):
    """Advanced text cleaning"""
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def clean_description(text):
    """Clean job description by removing UI/navigation clutter"""
    
    # LinkedIn UI patterns to remove
    linkedin_ui = [
        r'Skip to main content',
        r'LinkedIn.*?Apply',
        r'Promoted by.*?Responses managed',
        r'On-site.*?Full-time',
        r'Your profile is missing',
        r'Show match details',
        r'Help me update my profile',
        r'BETA.*?Is this information helpful',
        r'Messaging',
        r'This button displays',
        r'Expand search.*?This button',
        r'People also search',
        r'All filters',
        r'Easy Apply',
        r'Reset',
        r'Try the new job search',
    ]
    
    for pattern in linkedin_ui:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove navigation text
    nav_patterns = [
        r'Find jobs.*?Company Reviews.*?Find salaries',
        r'Sign in.*?Upload your resume',
        r'Post Job.*?Find jobs',
        r'→.*?Troubleshooting',
        r'Cloudflare Errors.*?Contact us',
        r'Enable JavaScript.*?Return home',
        r'Additional Verification Required',
    ]
    
    for pattern in nav_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Split into lines and filter
    lines = text.split('\n')
    cleaned_lines = []
    
    skip_keywords = [
        'skip to', 'linkedin', 'find jobs', 'company reviews', 'find salaries',
        'sign in', 'upload', 'post job', 'expand search', 'troubleshooting',
        'cloudflare', 'javascript', 'enable javascript', 'return home',
        'messaging', 'button displays', 'show more', 'currently selected',
        'this information', 'profile missing', 'qualifications', 'update profile',
        'beta', 'is this', 'all filters', 'easy apply', 'try the new',
        'upcoming earnings', 'people also search', 'expand', 'currently viewing'
    ]
    
    for line in lines:
        line = line.strip()
        
        # Skip empty
        if not line or len(line) < 3:
            continue
        
        # Skip if matches UI keywords
        if any(kw in line.lower() for kw in skip_keywords):
            continue
        
        # Skip if pure number or single character repeated
        if len(set(line)) == 1 or line.isdigit():
            continue
        
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)