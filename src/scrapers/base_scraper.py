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

            # 2. Enhanced anti-detection measures
            import random
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            ]
            selected_ua = random.choice(user_agents)
            chrome_options.add_argument(f"--user-agent={selected_ua}")
            
            # Disable blink features that reveal automation
            chrome_options.add_argument("--disable-blink-features")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")

            # General security bypasses (often needed for stubborn sites)
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--no-pings")
            import os
            proxy = os.getenv('SCRAPER_PROXY')
            if proxy:
                print(f"🔄 Proxy configuration detected. Routing scraper through proxy.")
                chrome_options.add_argument(f'--proxy-server={proxy}')

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
            
            # Additional common Windows paths for local testing
            if os.name == 'nt':
                possible_paths.extend([
                    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
                    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
                ])
            
            browser_path = next((p for p in possible_paths if p is not None and os.path.exists(p)), None)
            
            if browser_path:
                print(f"✅ Setting browser executable path to: {browser_path}")
            else:
                print(f"⚠️ Could not find browser executable in standard paths, letting undetected_chromedriver auto-detect.")
            
            # 5. Detect Chrome major version to prevent ChromeDriver version mismatch
            import subprocess
            version_main = None
            if browser_path:
                try:
                    if os.name == 'nt':
                        # Windows: use wmic or powershell to get version
                        result = subprocess.run(
                            ['powershell', '-Command', f'(Get-Item "{browser_path}").VersionInfo.FileVersion'],
                            capture_output=True, text=True, timeout=5
                        )
                    else:
                        # Linux: run the browser with --version flag
                        result = subprocess.run(
                            [browser_path, '--version'],
                            capture_output=True, text=True, timeout=5
                        )
                    
                    if result.stdout:
                        import re
                        version_match = re.search(r'(\d+)\.', result.stdout.strip())
                        if version_match:
                            version_main = int(version_match.group(1))
                            print(f"✅ Detected Chrome major version: {version_main}")
                except Exception as ver_err:
                    print(f"⚠️ Could not detect Chrome version: {ver_err}")
            
            # 3. Initialize Standard Selenium (Bypassing UC to avoid hangs)
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            
            # 3. Initialize memory-light but stealth-patched Chrome
            from selenium import webdriver
            
            print(f"  Launching memory-optimized stealth Chrome...")
            
            # Using standard webdriver with uc.ChromeOptions for lower RAM usage on Render
            if browser_path:
                chrome_options.binary_location = browser_path
                
            driver = webdriver.Chrome(options=chrome_options)

            # Increase timeouts significantly for slow Render cold-starts
            driver.set_page_load_timeout(60)
            driver.set_script_timeout(60)
            
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
    
    def validate_job_data(self, data):
        """Validate scraped job data"""
        required_fields = ['title', 'company', 'description', 'location']
        return all(data.get(field) for field in required_fields)