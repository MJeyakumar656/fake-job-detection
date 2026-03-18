from curl_cffi import requests
import json
import re

url = "https://www.naukri.com/job-listings-full-stack-developer-barclays-shared-services-chennai-0-to-9-years-160326502891"

print("Fetching URL with curl-cffi impersonating Chrome 120...")
try:
    # Impersonate a real browser TLS fingerprint
    response = requests.get(url, impersonate="chrome120", timeout=10)
    print("Status:", response.status_code)
    
    html = response.text
    print("Length:", len(html))
    
    # Check for Naukri identifiers
    print("Has INITIAL_STATE:", bool(re.search(r'__INITIAL_STATE__', html)))
    print("Has jobDetailsResp:", bool(re.search(r'jobDetailsResp', html)))
    
    # Check for Bot Protection
    if "Checking your browser" in html or "Cloudflare" in html:
        print("BLOCKED BY CLOUDFLARE JS CHALLENGE")
    else:
        print("SUCCESS! Body snippet:", html[1000:1200])
        
except Exception as e:
    print("FAILED:", e)
