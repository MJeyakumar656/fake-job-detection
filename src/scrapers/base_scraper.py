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
        """Initialize Stealth Selenium for bypassing Access Denied (Akamai/Cloudflare)"""
        import logging
        logger = logging.getLogger(__name__)
        try:
            import undetected_chromedriver as uc
            from selenium.webdriver.chrome.service import Service
            import shutil, os, random
            
            # Rotation of real browser UAs (anti-fingerprint)
            stealth_uas = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            ]
            ua = random.choice(stealth_uas)
            logger.info(f"Using stealth UA: {ua[:50]}...")
            
            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument(f'--user-agent={ua}')
            chrome_options.add_argument("--headless=new")  # Chromium 109+ stealth headless
            
            # ANTI-DETECTION FLAGS (critical for Naukri Access Denied)
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
# uc.Chrome() handles these internally - removed to fix "unrecognized chrome option: excludeSwitches"
            # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            # chrome_options.add_experimental_option('useAutomationExtension', False)

            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--disable-default-apps")
            
            # Performance/memory (Render-friendly)
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            
            # Render Chrome path (priority 1)
            render_chrome = '/opt/render/project/.render/chrome/opt/google/chrome/google-chrome'
            if os.path.exists(render_chrome):
                chrome_options.binary_location = render_chrome
                logger.info(f"Using Render Chrome: {render_chrome}")
            else:
                # Windows Chrome FIRST (test success ✅)
                chrome_paths = []
                if os.name == 'nt':
                    chrome_paths = [
                        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                        shutil.which('chrome'),
                        shutil.which('chromium')
                    ]
                chrome_paths += [shutil.which(p) for p in ['google-chrome', 'chromium-browser'] if shutil.which(p)]
                
                browser_path = next((p for p in chrome_paths if p and os.path.exists(p)), None)
                if browser_path:
                    logger.info(f"Chrome path: {browser_path}")
                    chrome_options.binary_location = browser_path
            
            # Prefs: No images/notifications
            prefs = {
                "profile.default_content_settings": {
                    "images": 2,
                    "notifications": 2
                }
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            logger.info("Creating stealth driver...")
            driver = uc.Chrome(options=chrome_options)  # uc auto-handles service
            
            # POST-LAUNCH STEALTH (after uc patches)
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                    window.chrome = {runtime: {}};
                """
            })
            
            driver.set_page_load_timeout(75)
            driver.set_script_timeout(75)
            
            logger.info("Stealth Selenium ready")
            print("✅ Enhanced Stealth Selenium ready")
            return driver
            
        except ImportError as ie:
            msg = f"ImportError (install deps): {ie}"
            logger.error(msg)
            raise Exception(msg)
        except FileNotFoundError as fnf:
            msg = f"Chrome missing: {fnf}"
            logger.error(msg)
            raise Exception(msg)
        except Exception as e:
            msg = f"Selenium init: {str(e)}"
            logger.error(msg, exc_info=True)
            raise Exception(msg)

    
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
            "access denied",
            "reference #",
            "you don't have permission to access",
            "the requested url was rejected",
            "please verify you are a human",
            "cloudflare ray id",
            "checking your browser before accessing",
            "let us know you're human",
            "let us know you’re human",
            "check the box to let us know"
        ]
        
        text_lower = text.lower()
        matched = []
        for marker in block_markers:
            if marker in text_lower:
                matched.append(marker)
                
        # Strong markers that instantly indicate a block
        strong_markers = [
            "access denied", 
            "let us know you're human", 
            "let us know you’re human",
            "check the box to let us know",
            "please verify you are a human",
            "checking your browser before accessing"
        ]
        
        if any(m in text_lower for m in strong_markers) or len(matched) >= 2:
            print(f"  🔍 [BlockCheck] DETECTED block page! Markers matched: {matched}")
            return True
        return False

    def _search_snippet_fallback(self, url, job_title="", company=""):
        """Last-resort fallback: Extract job details from search engine snippets."""
        print(f"🔍 [SearchFallback] {job_title} @ {company}")
        
        domain = self.get_domain(url)
        queries = [
            f'site:{domain} {job_title} {company}',
            f'{job_title} {company} {domain} job description'
        ]
        
        search_engine_templates = [
            "https://html.duckduckgo.com/html/?q={}",
            "https://www.bing.com/search?q={}"
        ]
        
        import cloudscraper
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
        
        for query in queries:
            q_encoded = requests.utils.quote(query)
            for template in search_engine_templates:
                search_url = template.format(q_encoded)
                try:
                    resp = scraper.get(search_url, timeout=10)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        
                        # Data we want to find
                        found_data = {
                            'description': None,
                            'title': None,
                            'company': None
                        }

                        # DuckDuckGo extraction
                        if "duckduckgo" in search_url:
                            results = soup.find_all('div', class_='result')
                            for r in results:
                                snippet_elem = r.find('a', class_='result__snippet')
                                title_elem = r.find('a', class_='result__a')
                                url_elem = r.find('a', class_='result__url')
                                
                                if snippet_elem and title_elem:
                                    # Validate: result URL must belong to the target domain
                                    result_url = ''
                                    if url_elem:
                                        result_url = url_elem.get('href', '') or url_elem.get_text()
                                    elif title_elem.get('href'):
                                        result_url = title_elem.get('href', '')
                                    
                                    if domain and domain not in result_url.lower():
                                        continue  # Skip unrelated results
                                    
                                    text = snippet_elem.get_text().strip()
                                    if len(text) > 80:
                                        print(f"✅ [SearchFallback] DuckDuckGo result found (domain-validated)")
                                        found_data['description'] = f"{text}\n\n[Extracted from Search Snippet]"
                                        return found_data
                        
                        # Bing extraction
                        elif "bing" in search_url:
                            results = soup.select('li.b_algo')
                            for r in results:
                                # Validate domain
                                link_elem = r.find('a')
                                result_url = link_elem.get('href', '') if link_elem else ''
                                if domain and domain not in result_url.lower():
                                    continue  # Skip unrelated results
                                
                                snippet_elem = r.find('p')
                                if snippet_elem:
                                    text = snippet_elem.get_text().strip()
                                    if len(text) > 80:
                                        print(f"✅ [SearchFallback] Bing result found (domain-validated)")
                                        found_data['description'] = f"{text}\n\n[Extracted from Search Snippet]"
                                        return found_data
                except Exception as e:
                    print(f"  ⚠️ [SearchFallback] Search failed for {search_url}: {e}")
                
        return None

    def get_domain(self, url):
        """Extract domain name from URL."""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        return domain.replace('www.', '')