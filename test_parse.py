from curl_cffi import requests
from bs4 import BeautifulSoup
import json
import re

url = "https://www.naukri.com/job-listings-full-stack-developer-barclays-shared-services-chennai-0-to-9-years-160326502891"

response = requests.get(url, impersonate="chrome120", timeout=10)
html = response.text
soup = BeautifulSoup(html, 'html.parser')

job_data = {}

for script in soup.find_all('script'):
    if script.string and 'jobDetailsResp' in script.string:
        try:
            # Look for "jobDetailsResp": { ... } inside the script
            # It's usually part of a larger window.__PRELOADED_STATE__ object
            match = re.search(r'\"jobDetailsResp\"\s*:\s*(\{.*?\})\s*(,|})', script.string, re.DOTALL)
            if match:
                data_str = match.group(1)
                
                # Check for nested json structure
                jd = json.loads(data_str)
                if 'jobDetails' in jd:
                    jd = jd['jobDetails']
                
                title = jd.get('title') or jd.get('jobTitle')
                print("Extracted Title:", title)
                
                raw_desc = jd.get('description') or jd.get('jobDescription') or ''
                if raw_desc:
                    desc = BeautifulSoup(raw_desc, "html.parser").get_text(separator="\\n").strip()
                    print("Extracted Description (len):", len(desc))
                    print("Snippet:", desc[:100])
                break
        except Exception as e:
            print("Parse error:", e)
