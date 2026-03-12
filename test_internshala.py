import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scrapers.internshala_scraper import InternshalaScraper

def test_internshala():
    url = "https://internshala.com/job/detail/fresher-client-service-specialist-job-in-farrukhabad-at-greenmint-finserve1771433770"
    scraper = InternshalaScraper()
    print("Testing Internshala Scraper...")
    try:
        data = scraper.scrape(url)
        print("Scrape Result:")
        for k, v in data.items():
            print(f"{k}: {str(v)[:100]}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_internshala()
