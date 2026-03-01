import requests
from bs4 import BeautifulSoup
import time
from abc import ABC, abstractmethod
from urllib.parse import urlparse

import os

# Try to import Selenium (optional dependency for server environments)
# Try to import Selenium (optional dependency for server environments)
SELENIUM_AVAILABLE = False
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    pass

class BaseScraper(ABC):
    """Base class for job portal scrapers"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        self.timeout = 15
    
    @property
    def has_selenium(self):
        """Check if Selenium/Chrome is available"""
        if not SELENIUM_AVAILABLE:
            return False
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(options=chrome_options)
            driver.quit()
            return True
        except Exception:
            return False
    
    def get_soup(self, url):
        """Get BeautifulSoup object from URL using requests"""
        try:
            timeout = 20 if 'linkedin.com' in url else self.timeout
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.Timeout:
            raise Exception(f"Timeout fetching {url}: Request took too long")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Connection error fetching {url}: Network issue")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error fetching {url}: {e.response.status_code}")
        except Exception as e:
            raise Exception(f"Failed to fetch {url}: {str(e)}")
    
    def get_page_text(self, url):
        """Get raw page text content using requests (lightweight fallback)"""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            
            return soup.get_text(separator='\n', strip=True), soup
        except Exception as e:
            raise Exception(f"Failed to fetch page: {str(e)}")
    
    def init_selenium_driver(self):
        """Initialize Selenium WebDriver (only if available)"""
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium is not available in this environment")
        
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage") # Critical for Render
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Additional aggressive memory-saving options for Render's 512MB limit
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-features=Translate")
            chrome_options.add_argument("--single-process") # Reduces memory footprint significantly
            chrome_options.add_argument("--js-flags=--max-old-space-size=128") # Strict V8 memory limit
            chrome_options.add_argument("--disk-cache-dir=/tmp/chrome-cache") # Use tmp instead of RAM
            chrome_options.page_load_strategy = 'eager' # Don't wait for images/CSS to finish loading completely
            
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            import random
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ]
            chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")

            # Use system chromium if available (Docker deployment)
            if os.path.exists('/usr/bin/chromium'):
                chrome_options.binary_location = '/usr/bin/chromium'
                service = Service(executable_path='/usr/bin/chromedriver')
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                driver = webdriver.Chrome(options=chrome_options)
                
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_page_load_timeout(30) # Shorter timeout for Render
            driver.set_script_timeout(20)
            return driver
        except Exception as e:
            raise Exception(f"Failed to initialize Selenium: {str(e)}")
    
    def extract_domain_from_url(self, url):
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ""
    
    def scrape_with_fallback(self, url, portal_name):
        """Scrape using requests first, fall back to Selenium if available"""
        # Try requests/BeautifulSoup first (works everywhere)
        try:
            print(f"  [Requests] Trying lightweight scraping for {portal_name}...")
            job_data = self.scrape_with_requests(url)
            if job_data and self.validate_job_data(job_data):
                print(f"  [Requests] Successfully scraped {portal_name} job data")
                return job_data
            print(f"  [Requests] Incomplete data, trying Selenium fallback...")
        except Exception as e:
            print(f"  [Requests] Failed: {str(e)}, trying Selenium fallback...")
        
        # Try Selenium if available
        if SELENIUM_AVAILABLE:
            try:
                print(f"  [Selenium] Trying browser-based scraping for {portal_name}...")
                job_data = self.scrape_with_selenium(url)
                if job_data and self.validate_job_data(job_data):
                    print(f"  [Selenium] Successfully scraped {portal_name} job data")
                    return job_data
                print(f"  [Selenium] Scraped data invalid. Bot protection prevented extraction.")
            except Exception as e:
                print(f"  [Selenium] Error during browser scraping: {str(e)}")
        
        # If we got partial data from requests, check if it's usable
        try:
            job_data = self.scrape_with_requests(url)
            if job_data and self.validate_job_data(job_data):
                return job_data
        except:
            pass
        
        raise Exception(
            f"Anti-Bot Protection Detected: {portal_name} blocks automated scanners. "
            "Please click the 'Text/Description' tab above and manually paste the job description to analyze it."
        )
    
    def scrape_with_requests(self, url):
        """Scrape using requests/BeautifulSoup (to be overridden by subclasses)"""
        raise NotImplementedError("Subclass must implement scrape_with_requests")
    
    def scrape_with_selenium(self, url):
        """Scrape using Selenium (to be overridden by subclasses)"""
        raise NotImplementedError("Subclass must implement scrape_with_selenium")
    
    @abstractmethod
    def scrape(self, url):
        """Scrape job posting from URL"""
        pass
    
    def validate_job_data(self, data):
        """Validate scraped job data"""
        if not data:
            return False
            
        # Check for empty or placeholder values
        title = data.get('title', '').strip()
        company = data.get('company', '').strip()
        description = data.get('description', '').strip()
        
        if not title or title == 'Unknown Job Title':
            return False
        if not company or company == 'Unknown Company':
            return False
        if not description or len(description) < 50:
            return False
            
        # Reject if we accidentally just scraped the No-JS boilerplate warning
        if 'browser does not support Javascript' in description or 'does not support Javascript' in description:
            return False
            
        return True