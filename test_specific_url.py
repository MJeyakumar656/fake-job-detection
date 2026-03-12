import sys
from pprint import pprint
import subprocess

# Force stdout to utf-8 in Windows
sys.stdout.reconfigure(encoding='utf-8')

from src.scrapers.scraper_manager import ScraperManager

def main():
    url = "https://www.naukri.com/job-listings-graduate-engineer-trainee-roots-group-of-companies-coimbatore-0-to-1-years-100326029611?src=drecomm_apply&sid=17733155575905936&xp=1&px=1"
    print(f"Testing URL: {url}\n")
    try:
        res = ScraperManager.scrape(url)
        print("\n=== FINAL RESULT ===")
        pprint(res)
    except Exception as e:
        print("\n=== FATAL ERROR ===")
        print(e)

if __name__ == "__main__":
    main()
