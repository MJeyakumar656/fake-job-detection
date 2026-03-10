import requests
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from abc import ABC, abstractmethod
from urllib.parse import urlparse

class BaseScraper(ABC):
    """Base class for job portal scrapers"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = 10
    
    def get_soup(self, url):
        """Get BeautifulSoup object from URL"""
        try:
            # Try with longer timeout for LinkedIn
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
    
    def init_selenium_driver(self):
        """Initialize Selenium WebDriver for JavaScript-heavy sites using undetected-chromedriver"""
        try:
            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument("--headless=new")
            
            # 1. Extreme Memory Saving Flags (Essential for Render's 512MB RAM limit)
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--single-process") # Forces single process
            chrome_options.add_argument("--js-flags=--max-old-space-size=256") # Limit JS engine memory
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-images")  # Don't load images for speed
            chrome_options.add_argument("--disable-background-networking")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--metrics-recording-only")
            chrome_options.add_argument("--mute-audio")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--window-size=1280,720") # Smaller window = less memory

            # 2. Enhanced anti-detection measures (mostly handled by undetected_chromedriver natively)
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            
            # 3. Proxy Configuration (Load from Environment Variables)
            import os
            proxy = os.getenv('SCRAPER_PROXY')
            if proxy:
                print(f"🔄 Proxy configuration detected. Routing scraper through proxy.")
                chrome_options.add_argument(f'--proxy-server={proxy}')

            # 4. Find the actual path to chromium or google-chrome
            import shutil
            import os
            # Try shutil first, then fallback to standard Linux installation paths used by Render
            browser_path = (
                shutil.which('chromium') or 
                shutil.which('chromium-browser') or 
                shutil.which('google-chrome') or 
                '/opt/render/project/.render/chrome/opt/google/chrome/google-chrome' or
                '/usr/bin/chromium'
            )
            
            if not os.path.exists(browser_path) and browser_path == '/usr/bin/chromium':
                browser_path = '/usr/bin/google-chrome'

            print(f"✅ Setting browser executable path to: {browser_path}")
            
            # CRITICAL FIX FOR UNDETECTED CHROMEDRIVER ON RENDER
            # undetected_chromedriver has a bug where it auto-detects Chrome instead of Chromium 
            # and throws "Could not determine browser executable" if Chrome isn't found,
            # EVEN IF we pass browser_executable_path via kwargs.
            # We must monkeypatch uc.find_chrome_executable
            
            original_find_chrome = uc.find_chrome_executable
            
            try:
                # Force the patcher to always return our detected path
                uc.find_chrome_executable = lambda: browser_path
                
                driver_kwargs = {
                    "options": chrome_options,
                    "browser_executable_path": browser_path,
                    "use_subprocess": True, # Helps prevent detached process issues in Docker
                }
    
                try:
                    driver = uc.Chrome(**driver_kwargs)
                except TypeError as e:
                    if "expected str, bytes or os.PathLike object, not NoneType" in str(e) or "Must be a String" in str(e):
                        print("⚠️ Undetected-chromedriver rejected the path. Forcing initialization bypass...")
                        class PatchedChrome(uc.Chrome):
                            def __init__(self, *args, **kwargs):
                                kwargs['browser_executable_path'] = browser_path
                                super().__init__(*args, **kwargs)
                                
                        driver = PatchedChrome(**driver_kwargs)
                    else:
                        raise e
            finally:
                # Always restore the original function
                uc.find_chrome_executable = original_find_chrome

            # Increase timeouts significantly for slow Render cold-starts
            driver.set_page_load_timeout(30)
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
    
    @abstractmethod
    def scrape(self, url):
        """Scrape job posting from URL"""
        pass
    
    def validate_job_data(self, data):
        """Validate scraped job data"""
        required_fields = ['title', 'company', 'description', 'location']
        return all(data.get(field) for field in required_fields)