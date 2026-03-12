import sys
import json
import traceback

from src.scrapers.indeed_scraper import IndeedScraper
from src.scrapers.naukri_scraper import NaukriScraper

def test_urls():
    urls = [
        ("Naukri", "https://www.naukri.com/job-listings-java-developer-siri-tech-solutions-hyderabad-chennai-bengaluru-0-to-1-years-090326028677?src=drecomm_apply&sid=17731470218436452&xp=1&px=1"),
        ("Indeed", "https://in.indeed.com/viewjob?jk=ec40ba61442d3b5b&from=shareddesktop_copy")
    ]
    
    for name, url in urls:
        print(f"\n{'='*40}")
        print(f"Testing {name} URL: {url}")
        print(f"{'='*40}")
        
        try:
            if name == "Naukri":
                scraper = NaukriScraper()
            else:
                scraper = IndeedScraper()
                
            result = scraper.scrape(url)
            
            print(f"\nResult format valid: {isinstance(result, dict)}")
            
            for key in ["title", "company", "location", "description"]:
                val = result.get(key)
                if val:
                    preview = val[:100].replace('\n', ' ') + "..." if len(str(val)) > 100 else val
                    print(f"- {key}: {preview}")
                else:
                    print(f"- {key}: MISSING OR EMPTY ❌")
                    
        except Exception as e:
            print(f"\n❌ Scraping Failed: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    test_urls()
