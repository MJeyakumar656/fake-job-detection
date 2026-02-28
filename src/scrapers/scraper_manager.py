from src.scrapers.linkedin_scraper import LinkedInScraper
from src.scrapers.naukri_scraper import NaukriScraper
from src.scrapers.indeed_scraper import IndeedScraper
from src.scrapers.internshala_scraper import InternshalaScraper

class ScraperManager:
    """Manage all job portal scrapers"""
    
    SCRAPERS = {
        'linkedin.com': LinkedInScraper,
        'naukri.com': NaukriScraper,
        'indeed.com': IndeedScraper,
        'internshala.com': InternshalaScraper,
    }
    
    @staticmethod
    def scrape(url):
        """Automatically detect portal and scrape"""
        print(f"🔍 Detecting job portal from URL: {url}")
        
        # Detect portal
        portal = None
        for portal_name in ScraperManager.SCRAPERS.keys():
            if portal_name in url.lower():
                portal = portal_name
                break
        
        if not portal:
            raise Exception("Unsupported job portal. Supported: LinkedIn, Naukri, Indeed, Internshala")
        
        print(f"✓ Detected portal: {portal}")
        
        # Initialize appropriate scraper
        scraper_class = ScraperManager.SCRAPERS[portal]
        scraper = scraper_class()
        
        # Scrape job data
        job_data = scraper.scrape(url)
        
        return job_data