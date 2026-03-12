import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scrapers.indeed_scraper import IndeedScraper

def test_indeed():
    url = "https://www.indeed.com/viewjob?jk=1234567890abcdef" # dummy ID just to see what html requests gets
    scraper = IndeedScraper()
    print("Testing Indeed Scraper...")
    try:
        data = scraper.scrape(url)
        print("Scrape Result:")
        for k, v in data.items():
            print(f"{k}: {str(v)[:100]}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_indeed()
