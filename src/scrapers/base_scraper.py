import requests
from bs4 import BeautifulSoup
import time
from abc import ABC, abstractmethod
from urllib.parse import urlparse

import os

# Try to import Selenium (optional dependency for server environments)
SELENIUM_AVAILABLE = False
if not os.environ.get('RENDER'):
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
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
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            import random
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ]
            chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")

            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_page_load_timeout(45)
            driver.set_script_timeout(30)
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
                return self.scrape_with_selenium(url)
            except Exception as e:
                raise Exception(f"Both scraping methods failed for {portal_name}: {str(e)}")
        
        # If we got partial data from requests, return it anyway
        try:
            job_data = self.scrape_with_requests(url)
            if job_data:
                return job_data
        except:
            pass
        
        raise Exception(f"Could not scrape {portal_name} job data. Chrome is not available on this server for JavaScript-heavy pages.")
    
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
        required_fields = ['title', 'company', 'description', 'location']
        return all(data.get(field) for field in required_fields)