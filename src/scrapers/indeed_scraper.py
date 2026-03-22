from src.scrapers.base_scraper import BaseScraper
import json
import re
import urllib.parse
import cloudscraper
import requests
from bs4 import BeautifulSoup


class IndeedScraper(BaseScraper):
    """Scraper for Indeed.com job postings — multi-tier extraction.

    Tier 1: Mobile API (less strict Cloudflare)
    Tier 2: Cloudscraper HTML (JSON-LD + HTML selectors)
    Tier 3: Selenium headless Chrome
    """

    # ------------------------------------------------------------------ #
    #  Public entry point
    # ------------------------------------------------------------------ #
    def scrape(self, url):
        """Scrape Indeed job posting using a three-tier strategy."""
        print("🔗 Scraping Indeed job posting...")

        if 'indeed.com' not in url:
            raise Exception("Invalid Indeed URL")

        # Extract Indeed job ID from URL
        job_id = self._extract_job_id(url)
        print(f"📋 Extracted job ID: {job_id or 'N/A'}")

        # ---------- Tier 1: Mobile API ----------
        if job_id:
            try:
                print("🔄 [Tier 1] Trying Indeed mobile API...")
                result = self._scrape_via_mobile_api(url, job_id)
                if self._is_valid_result(result):
                    print("✅ [Tier 1] Mobile API scraping successful")
                    return result
                else:
                    print("⚠️ [Tier 1] Mobile API returned incomplete data")
            except Exception as e:
                print(f"❌ [Tier 1] Mobile API failed: {e}")

        # ---------- Tier 2: Cloudscraper HTML ----------
        try:
            print("🔄 [Tier 2] Trying cloudscraper HTML scraping...")
            result = self._scrape_via_cloudscraper(url)
            if self._is_valid_result(result):
                print("✅ [Tier 2] Cloudscraper scraping successful")
                return result
        except Exception as e:
            print(f"❌ [Tier 2] Cloudscraper failed: {e}")

        # ---------- Tier 2.5: Google Cache fallback ----------
        try:
            print("🔄 [Tier 2.5] Attempting Google Cache fetch...")
            # Reuse the job_id if we have it for cache query
            cache_url = f"http://webcache.googleusercontent.com/search?q=cache:{url}"
            scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
            resp = scraper.get(cache_url, timeout=12)
            if resp.status_code == 200:
                result = self._parse_html_content(resp.content, url)
                if self._is_valid_result(result):
                    print("✅ [Tier 2.5] Google Cache scraping successful")
                    return result
        except Exception as e:
            print(f"❌ [Tier 2.5] Google Cache failed: {e}")

        # ---------- Tier 3: Selenium fallback ----------
        try:
            print("🔄 [Tier 3] Trying Selenium fallback...")
            result = self._scrape_via_selenium(url)
            if self._is_valid_result(result):
                print("✅ [Tier 3] Selenium scraping successful")
                return result
        except Exception as e:
            print(f"❌ [Tier 3] Selenium failed: {e}")

        # ---------- All tiers failed ----------
        print("❌ All scraping methods failed for Indeed")
        # Return a warning result rather than an outright error
        # This will still trigger our AI analysis but correctly display a manual action warning
        return self._error_result(
            url,
            "Indeed's security system blocked automation. Please click the 'Text / Description' tab and manually paste the job description to run the AI analysis."
        )

    # ------------------------------------------------------------------ #
    #  Tier 1 — Mobile API
    # ------------------------------------------------------------------ #
    def _scrape_via_mobile_api(self, url, job_id):
        """Try Indeed's mobile/embedded viewjob API."""
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )

        # Try multiple Indeed API variants
        api_urls = [
            f"https://www.indeed.com/m/basecamp/viewjob?viewtype=embedded&jk={job_id}",
            f"https://in.indeed.com/m/basecamp/viewjob?viewtype=embedded&jk={job_id}",
        ]

        for api_url in api_urls:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 '
                                  '(KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
                    'Accept': 'application/json',
                }
                resp = scraper.get(api_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    return self._parse_mobile_api(data, url)
            except Exception:
                continue

        raise Exception("Mobile API not accessible")

    def _parse_mobile_api(self, data, url):
        """Parse Indeed mobile API JSON response."""
        job_data = self._empty_result(url)

        if 'jobTitle' in data:
            job_data['title'] = data['jobTitle']
        if 'companyInfo' in data and 'companyName' in data['companyInfo']:
            job_data['company'] = data['companyInfo']['companyName']
        if 'jobDescriptionText' in data:
            job_data['description'] = BeautifulSoup(
                data['jobDescriptionText'], "html.parser"
            ).get_text(separator="\n").strip()
        if 'jobLocation' in data:
            job_data['location'] = data['jobLocation']

        return job_data

    # ------------------------------------------------------------------ #
    #  Tier 2 — Cloudscraper HTML
    # ------------------------------------------------------------------ #
    def _scrape_via_cloudscraper(self, url):
        """Scrape Indeed page HTML using cloudscraper to bypass Cloudflare."""
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

        response = scraper.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        return self._parse_html_content(response.content, url)

    def _parse_html_content(self, html_content, url):
        """Extract job data from Indeed HTML content (JSON-LD + Selectors)."""
        soup = BeautifulSoup(html_content, 'html.parser')
        job_data = self._empty_result(url)

        # --- JSON-LD structured data ---
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                    if data.get('title'):
                        job_data['title'] = data['title']
                    if data.get('description'):
                        job_data['description'] = BeautifulSoup(
                            data['description'], "html.parser"
                        ).get_text(separator="\n").strip()
                    if 'hiringOrganization' in data:
                        org = data['hiringOrganization']
                        if isinstance(org, dict):
                            job_data['company'] = org.get('name', job_data['company'])
                            if org.get('sameAs'):
                                job_data['company_domain'] = self.extract_domain_from_url(org['sameAs'])
                    if 'jobLocation' in data:
                        loc = data['jobLocation']
                        if isinstance(loc, dict) and 'address' in loc:
                            addr = loc['address']
                            city = addr.get('addressLocality', '')
                            region = addr.get('addressRegion', '')
                            job_data['location'] = f"{city}, {region}".strip(', ')
                    if 'baseSalary' in data:
                        salary = data['baseSalary']
                        if isinstance(salary, dict) and 'value' in salary:
                            val = salary['value']
                            if isinstance(val, dict):
                                job_data['salary'] = (
                                    f"{val.get('minValue', '')} - "
                                    f"{val.get('maxValue', '')} "
                                    f"{val.get('unitText', '')}"
                                )
                    break
            except Exception:
                continue

        # --- HTML selector fallbacks ---
        if job_data['title'] == 'Unknown Job Title':
            title_elem = (
                soup.select_one("h1.jobsearch-JobInfoHeader-title") or
                soup.select_one("h1[class*='JobTitle']") or
                soup.find("h1")
            )
            if title_elem:
                job_data['title'] = title_elem.get_text().strip()

        if job_data['company'] == 'Unknown Company':
            comp_elem = (
                soup.select_one("div[data-company-name='true']") or
                soup.select_one("span[data-testid='company-name']") or
                soup.select_one("div[class*='CompanyName']")
            )
            if comp_elem:
                job_data['company'] = comp_elem.get_text().strip()

        if job_data['location'] == 'Not Specified':
            loc_elem = (
                soup.select_one("div[data-testid='inlineHeader-companyLocation']") or
                soup.select_one("div[data-testid='job-location']") or
                soup.select_one("div[class*='CompanyLocation']")
            )
            if loc_elem:
                job_data['location'] = loc_elem.get_text().strip()

        if job_data['description'] == 'No description available':
            desc_elem = (
                soup.select_one("div#jobDescriptionText") or
                soup.select_one("div.jobsearch-jobDescriptionText") or
                soup.select_one("div[class*='JobDescription']")
            )
            if desc_elem:
                job_data['description'] = desc_elem.get_text(separator="\n").strip()

        return job_data

    # ------------------------------------------------------------------ #
    #  Tier 3 — Selenium fallback
    # ------------------------------------------------------------------ #
    def _scrape_via_selenium(self, url):
        """Use headless Chrome to render the Indeed page and extract content."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time

        driver = None
        try:
            # Initialize driver using base class method
            driver = self.init_selenium_driver()
            
            # Randomize delay to mimic human behavior
            import random
            print(f"  🌍 Navigating to Indeed (Stealth Mode)...")
            
            # Sometimes a direct hit triggers Cloudflare; try hitting home first
            if random.random() > 0.5:
                driver.get("https://in.indeed.com/")
                time.sleep(random.uniform(2, 4))
            
            driver.get(url)
            
            # CRITICAL: Wait for Cloudflare/antibot JS challenge to resolve
            print("  ⏳ Waiting for potential Cloudflare challenge to resolve...")
            time.sleep(10) # Increased for Render

            # Detect Cloudflare or block pages immediately
            page_source = driver.page_source.lower()
            if "cloudflare" in page_source or "please enable cookies" in page_source or "human verification" in page_source:
                print("  🛑 Indeed blocked the automated session (Cloudflare detected)")
                raise Exception("Indeed blocked automation. Cloudflare challenge detected.")

            # Wait for key content to render
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                        "h1, h2, div#jobDescriptionText, div[class*='jobsearch-JobInfoHeader'], [data-testid*='JobTitle']"))
                )
            except Exception:
                print("  ⚠️ Selenium wait timeout, continuing with whatever loaded...")

            time.sleep(5)

            job_data = self._empty_result(url)
            job_data['url'] = driver.current_url

            # --- Title ---
            title_selectors = [
                "h1.jobsearch-JobInfoHeader-title",
                "h2.jobsearch-JobInfoHeader-title",
                "[data-testid='jobsearch-JobInfoHeader-title']",
                "h1[class*='JobTitle']",
                "h2[class*='jobTitle']",
                "h1",
            ]
            for sel in title_selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, sel)
                    if elem.text.strip():
                        job_data['title'] = elem.text.strip()
                        break
                except Exception:
                    continue

            # --- Company ---
            company_selectors = [
                "div.jobsearch-InlineCompanyRating a",
                "[data-testid='inline-company-link']",
                "div[data-company-name='true'] a",
                "div[data-company-name='true']",
                "span[data-testid='company-name']",
                "div[class*='CompanyName']",
            ]
            for sel in company_selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, sel)
                    if elem.text.strip():
                        job_data['company'] = elem.text.strip()
                        break
                except Exception:
                    continue

            # --- Location ---
            location_selectors = [
                "div.jobsearch-JobInfoHeader-subtitle > div:nth-child(2)",
                "div[data-testid='inlineHeader-companyLocation']",
                "div[data-testid='job-location']",
                "div[class*='CompanyLocation']",
            ]
            for sel in location_selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, sel)
                    if elem.text.strip():
                        job_data['location'] = elem.text.strip()
                        break
                except Exception:
                    continue

            # --- Description ---
            desc_selectors = [
                "div#jobDescriptionText",
                "div.jobsearch-jobDescriptionText",
                "div[class*='JobDescription']",
                "section[class*='jobDescription']",
                "div[class*='details-section']",
            ]
            for sel in desc_selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, sel)
                    if elem.text.strip() and len(elem.text.strip()) > 50:
                        job_data['description'] = elem.text.strip()
                        break
                except Exception:
                    continue

            # --- [Tier 3.5] Last Ghasp Body Scan ---
            if job_data['description'] == 'No description available' or job_data['title'] == 'Unknown Job Title':
                print("  ⚠️ Selectors failed. Running 'Last Ghasp' body scan...")
                try:
                    body_text = driver.find_element(By.TAG_NAME, "body").text
                    
                    # Title Recovery
                    if job_data['title'] == 'Unknown Job Title':
                        lines = [l.strip() for l in body_text.split("\n") if len(l.strip()) > 5]
                        if lines: job_data['title'] = lines[0] # Grab first non-empty line
                    
                    # Description Recovery
                    if job_data['description'] == 'No description available':
                        # Look for common headers
                        markers = ["Job details", "Full job description", "About the job"]
                        for marker in markers:
                            if marker in body_text:
                                potential = body_text.split(marker, 1)[1].split("Hiring Lab", 1)[0].strip()
                                if len(potential) > 200:
                                    job_data['description'] = potential
                                    break
                        
                        # Fallback to largest block
                        if job_data['description'] == 'No description available':
                            blocks = body_text.split("\n\n")
                            best = max(blocks, key=len, default="")
                            if len(best) > 200:
                                job_data['description'] = best
                except Exception as e:
                    print(f"  ⚠️ Last Ghasp failed: {e}")

            return job_data

        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #
    def _extract_job_id(self, url):
        """Extract Indeed job ID (jk parameter) from URL."""
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)

        # Try common Indeed ID parameters
        for key in ('vjk', 'jk', 'fccid'):
            if key in params:
                return params[key][0]

        # Try extracting from URL path (e.g. /viewjob/abc123)
        match = re.search(r'/viewjob/([a-zA-Z0-9]+)', url)
        if match:
            return match.group(1)

        return None

    def _empty_result(self, url):
        """Return a job_data dict with default empty values."""
        return {
            'title': 'Unknown Job Title',
            'company': 'Unknown Company',
            'company_domain': '',
            'location': 'Not Specified',
            'description': 'No description available',
            'requirements': '',
            'job_type': '',
            'salary': '',
            'job_portal': 'indeed.com',
            'url': url,
        }

    def _error_result(self, url, message):
        """Return an error result with guidance for the user."""
        result = self._empty_result(url)
        result['title'] = 'Extraction Failed'
        result['company'] = 'Extraction Failed'
        result['location'] = 'Extraction Failed'
        result['description'] = message
        result['error'] = message
        return result

    def _is_valid_result(self, result):
        """Check if a scraping result has meaningful data (v2.1)."""
        # 1. Check for block pages
        desc = result.get('description', '')
        if self._is_blocked_page(desc):
            return False

        # 2. Check for minimum required content
        has_title = result.get('title', '').strip() not in ('', 'Unknown Job Title', 'Extraction Failed')
        has_desc = (
            result.get('description', '').strip() not in ('', 'No description available', 'Extraction Failed')
            and len(result.get('description', '')) > 50
        )
        return has_title or has_desc