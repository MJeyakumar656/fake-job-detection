from curl_cffi import requests
from bs4 import BeautifulSoup
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

url = "https://www.naukri.com/job-listings-full-stack-developer-barclays-shared-services-chennai-0-to-9-years-160326502891"
response = requests.get(url, impersonate="chrome120", timeout=10)
soup = BeautifulSoup(response.text, 'html.parser')

print("Title:", soup.title.string if soup.title else "None")

title_meta = soup.find('meta', attrs={'property': 'og:title'})
if title_meta:
    print("OG Title:", title_meta.get('content'))

desc_meta = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
if desc_meta:
    print("OG Description:", desc_meta.get('content'))

# Any other LD+JSON?
for script in soup.find_all('script', type='application/ld+json'):
    print("Found LD+JSON!")
    print(script.string[:500])
