import urllib.request
import urllib.error
import urllib.parse

url = "https://www.naukri.com/job-listings-full-stack-developer-barclays-shared-services-chennai-0-to-9-years-160326502891"

req = urllib.request.Request(
    url, 
    headers={
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
)

try:
    print("Fetching mobile HTML...")
    html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
    print("SUCCESS! Length:", len(html))
    import re
    print("Has INITIAL_STATE:", bool(re.search(r'__INITIAL_STATE__', html)))
    print("Has jobDetailsResp:", bool(re.search(r'jobDetailsResp', html)))
except Exception as e:
    print("Failed:", e)
