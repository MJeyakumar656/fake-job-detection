import requests
from bs4 import BeautifulSoup
import cloudscraper
import json

def test_naukri(url):
    print("--- Naukri ---")
    scraper = cloudscraper.create_scraper()
    resp = scraper.get(url)
    print("Status:", resp.status_code)
    soup = BeautifulSoup(resp.text, 'html.parser')
    for script in soup.find_all('script', type='application/ld+json'):
        if 'JobPosting' in script.text:
            print("Found JobPosting JSON-LD!")
            data = json.loads(script.text)
            print("Title:", data.get('title'))
            return
    print("No JSON-LD JobPosting found.")
    h1 = soup.find('h1')
    if h1: print("H1:", h1.text)

def test_internshala(url):
    print("--- Internshala ---")
    scraper = cloudscraper.create_scraper()
    resp = scraper.get(url)
    print("Status:", resp.status_code)
    soup = BeautifulSoup(resp.text, 'html.parser')
    text = soup.get_text()
    if 'does not support Javascript' in text:
        print("Blocked by JS requirement!")
    else:
        print("Success! JS requirement bypassed or not present.")
        h1 = soup.find('h1')
        if h1: print("H1:", h1.text)

if __name__ == "__main__":
    naukri_url = "https://www.naukri.com/job-listings-senior-software-engineer-google-inc-mumbai-delhi-ncr-bengaluru-hyderabad-pune-chennai-7-to-12-years-150223500356"
    internshala_url = "https://internshala.com/job/detail/associate-front-end-developer-remote-fresher-job-at-tripple-one-solutions1740612185"
    try:
        test_naukri(naukri_url)
    except Exception as e: print("Naukri failed:", e)
    try:
        test_internshala(internshala_url)
    except Exception as e: print("Internshala failed:", e)
