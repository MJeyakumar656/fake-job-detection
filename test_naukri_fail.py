import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.scrapers.scraper_manager import ScraperManager
from src.analyzer import JobAnalyzer
import sys
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test():
    manager = ScraperManager()
    url = "https://www.naukri.com/job-listings-fake-job-000000000000"
    
    print("Scraping...")
    # Monkey patch print to avoid encoding errors deeper in the code
    import builtins
    old_print = builtins.print
    def safe_print(*args, **kwargs):
        try:
            old_print(*args, **kwargs)
        except UnicodeEncodeError:
            old_print("Unicode print error caught", **kwargs)
    builtins.print = safe_print
    
    job_data = manager.scrape(url)
    
    print("\nScraper Result:")
    print(json.dumps(job_data, indent=2))
    
    analyzer = JobAnalyzer()
    print("\nRunning Analyzer...")
    analysis = analyzer._analyze_job_data(job_data)
    
    print("\nAnalysis Result:")
    print(json.dumps(analysis, indent=2))

if __name__ == "__main__":
    test()
