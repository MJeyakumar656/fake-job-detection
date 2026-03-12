import sys
import time
from src.scrapers.scraper_manager import ScraperManager

def test_naukri():
    # A sample Naukri URL
    naukri_url = "https://www.naukri.com/job-listings-python-developer-indiafilings-chennai-0-to-3-years-020326030847"
    
    print("--- 1st Attempt ---")
    try:
        res1 = ScraperManager.scrape(naukri_url)
        print("Result 1:", res1.get('title'), res1.get('company'))
    except Exception as e:
        print("Error 1:", e)
        
    print("\nWaiting 2 seconds...\n")
    time.sleep(2)
    
    print("--- 2nd Attempt ---")
    try:
        res2 = ScraperManager.scrape(naukri_url)
        print("Result 2:", res2.get('title'), res2.get('company'))
    except Exception as e:
        print("Error 2:", e)

if __name__ == "__main__":
    test_naukri()
