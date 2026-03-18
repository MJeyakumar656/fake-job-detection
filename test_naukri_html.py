import cloudscraper

url = "https://www.naukri.com/job-listings-full-stack-developer-barclays-shared-services-chennai-0-to-9-years-160326502891"

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
)

resp = scraper.get(url, timeout=15)
print(f"Status: {resp.status_code}")

html = resp.text
import re

# Look for various JSON blobs
print("JSON-LD found:", bool(re.search(r'type=["\']application/ld\+json["\']', html)))
print("INITIAL_STATE found:", bool(re.search(r'__INITIAL_STATE__', html)))
print("jobDetailsResp found:", bool(re.search(r'jobDetailsResp', html)))

# Save html snippet
with open('naukri_dump.html', 'w', encoding='utf-8') as f:
    f.write(html)
