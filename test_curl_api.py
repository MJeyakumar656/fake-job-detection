from curl_cffi import requests

api_url = "https://www.naukri.com/jobapi/v3/job/160326502891"

headers = {
    'appid': '109',
    'systemid': 'Naukri',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Referer': 'https://www.naukri.com/job-listings-full-stack-developer-barclays-shared-services-chennai-0-to-9-years-160326502891?src=drecomm_apply&sid=17738482437634715&xp=10&px=1',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'clientid': 'd3ti',
}

session = requests.Session(impersonate="chrome120")

print("Fetching home page for cookies...")
try:
    session.get("https://www.naukri.com/", timeout=10)
    print("Got cookies!")
except Exception as e:
    print("Failed to get cookies:", e)

print("Fetching API directly...")
try:
    response = session.get(api_url, headers=headers, timeout=10)
    print("API Status:", response.status_code)
    
    if response.status_code == 200:
        data = response.json()
        jd = data.get('jobDetails', {})
        print("Success! Title:", jd.get('title', 'Unknown'))
        print("Company:", jd.get('companyDetail', {}).get('name', 'Unknown'))
    else:
        print("API Failed:", response.text[:200])
except Exception as e:
    print("API Call Error:", e)
