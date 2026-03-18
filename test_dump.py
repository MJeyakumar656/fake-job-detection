from curl_cffi import requests

url = "https://www.naukri.com/job-listings-full-stack-developer-barclays-shared-services-chennai-0-to-9-years-160326502891"
response = requests.get(url, impersonate="chrome120", timeout=10)

with open('naukri_dump.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
print("Dumped")
