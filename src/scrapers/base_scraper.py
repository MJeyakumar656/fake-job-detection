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
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-infobars")
            
            # 1. Extreme Memory Saving Flags (Essential for Render's 512MB RAM limit)
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-browser-side-navigation")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--dns-prefetch-disable")
            
            # Additional flags for uc stability in Docker
            chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
            chrome_options.add_argument("--blink-settings=imagesEnabled=false") # Save bandwidth/RAM
            chrome_options.add_argument("--js-flags=--max-old-space-size=256") # Limit JS engine memory
            # Aggressive Resource Disabling for Render (512MB RAM)
            chrome_options.add_argument("--disable-webgl")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-javascript-harmony-shipping")
            chrome_options.add_argument("--disable-plugins-discovery")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-breakpad")
            chrome_options.add_argument("--disable-component-update")
            chrome_options.add_argument("--disable-domain-reliability")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            chrome_options.add_argument("--disable-print-preview")
            chrome_options.add_argument("--disable-hang-monitor")
            chrome_options.add_argument("--no-pings")
            chrome_options.add_argument("--mute-audio")
            
            # Memory limits
            # Lowering max space size to give the OS more breathing room on Render
            chrome_options.add_argument("--js-flags=--max-old-space-size=128") 
            
            # Disable image loading completely via prefs
            prefs = {
                "profile.managed_default_content_settings.images": 2, 
                "profile.default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
            }
            chrome_options.add_experimental_option("prefs", prefs)

            # 4. Find the actual path to chromium or google-chrome
            import shutil
            import os
            
            # Possible paths to check (Render custom path, then system defaults)
            possible_paths = [
                '/opt/render/project/.render/chrome/opt/google/chrome/google-chrome',
                shutil.which('chromium'),
                shutil.which('chromium-browser'),
                shutil.which('google-chrome'),
                '/usr/bin/chromium',
                '/usr/bin/google-chrome'
            ]
            
            if os.name == 'nt':
                possible_paths.extend([
                    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
                ])
            
            browser_path = next((p for p in possible_paths if p is not None and os.path.exists(p)), None)
            
            if browser_path:
                print(f"✅ Setting browser executable path to: {browser_path}")
                chrome_options.binary_location = browser_path
            
            # 5. Initialize memory-light but stealth-patched Chrome
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            
            print(f"  Launching memory-optimized stealth Chrome...")
            
            driver = webdriver.Chrome(options=chrome_options)

            # Increase timeouts significantly for slow Render cold-starts
            driver.set_page_load_timeout(90) # Increased to 90s
            driver.set_script_timeout(90)
            
            # Execute CDP commands to hide webdriver flag effectively
            try:
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                        // Hide automation flags
                        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                        window.chrome = { runtime: {} };
                        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                    """
                })
            except Exception as e:
                print(f"⚠️ Could not execute CDP command: {e}")

            return driver
        except Exception as e:
            raise Exception(f"Failed to initialize Selenium (Light): {str(e)}")
    
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
    
    def _is_valid_result(self, result):
        """Standard validation for all scrapers (existence + quality + block detection)."""
        if not result: return False
        
        title = result.get('title', '')
        company = result.get('company', '')
        desc = result.get('description', '')
        
        # 1. Block Page Check (Highest Priority)
        if self._is_blocked_page(title) or self._is_blocked_page(desc) or self._is_blocked_page(company):
            print(f"  🛑 [BaseScraper] Blocked page detected in content. Invalidating tier result.")
            return False
            
        # 2. Existence Check
        has_title = title.strip() not in ('', 'Unknown Job Title', 'Extraction Failed', 'Access Denied')
        has_desc = (
            desc.strip() not in ('', 'No description available', 'Extraction Failed', 'Access Denied')
            and len(desc) > 50
        )
        
        if not (has_title or has_desc):
            print(f"  ⚠️ [BaseScraper] Incomplete/placeholder data. Title='{title[:20]}...', DescLen={len(desc)}")
            return False
            
        return True

    def validate_job_data(self, data):
        """Compatibility wrapper for validate_job_data."""
        return self._is_valid_result(data)

    def _is_blocked_page(self, text):
        """Check if the extracted text belongs to a block page (Akamai/Cloudflare)."""
        if not text: return False
        
        block_markers = [
            "Access Denied",
            "Reference #",
            "You don't have permission to access",
            "The requested URL was rejected",
            "Please verify you are a human",
            "Cloudflare ray ID",
            "checking your browser before accessing"
        ]
        
        count = 0
        text_lower = text.lower()
        matched = []
        for marker in block_markers:
            if marker.lower() in text_lower:
                count += 1
                matched.append(marker)
                
        # If we see multiple markers or "Access Denied" specifically
        if "access denied" in text_lower or count >= 2:
            print(f"  🔍 [BlockCheck] DETECTED block page! Markers matched: {matched}")
            return True
        return False