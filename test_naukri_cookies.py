import cloudscraper
import json

url = "https://www.naukri.com/job-listings-full-stack-developer-barclays-shared-services-chennai-0-to-9-years-160326502891?src=drecomm_apply&sid=17738482437634715&xp=10&px=1"
job_id = "160326502891"
api_url = f"https://www.naukri.com/jobapi/v3/job/{job_id}"

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
)

print("Fetching job page to establish cookies...")
page_resp = scraper.get(url, timeout=10)
print(f"Page Status: {page_resp.status_code}")

print("\nFetching API...")
headers = {
    'appid': '109',
    'systemid': 'Naukri',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Referer': f'https://www.naukri.com/job-listings-{job_id}',
}

api_resp = scraper.get(api_url, headers=headers, timeout=10)
print(f"API Status: {api_resp.status_code}")

if api_resp.status_code == 200:
    print("SUCCESS")
else:
    print("FAILED:", api_resp.text[:200])
