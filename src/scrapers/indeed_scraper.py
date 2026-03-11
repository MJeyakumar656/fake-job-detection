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
            else:
                print("⚠️ [Tier 2] Cloudscraper returned incomplete data")
        except Exception as e:
            print(f"❌ [Tier 2] Cloudscraper failed: {e}")

        # ---------- Tier 3: Selenium fallback ----------
        try:
            print("🔄 [Tier 3] Trying Selenium fallback...")
            result = self._scrape_via_selenium(url)
            if self._is_valid_result(result):
                print("✅ [Tier 3] Selenium scraping successful")
                return result
            else:
                print("⚠️ [Tier 3] Selenium returned incomplete data")
                # Return whatever we got
                if result.get('description', 'No description available') != 'No description available':
                    return result
        except Exception as e:
            print(f"❌ [Tier 3] Selenium failed: {e}")

        # ---------- All tiers failed ----------
        print("❌ All scraping methods failed for Indeed")
        return self._error_result(
            url,
            "Indeed is blocking automated scraping. Please copy and paste "
            "the Job Title, Company, and Description manually using the "
            "Text/Description tab."
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

        soup = BeautifulSoup(response.content, 'html.parser')
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
            driver = self.init_selenium_driver()
            driver.get(url)
            
            # CRITICAL: Wait for Cloudflare/antibot JS challenge to resolve
            print("  ⏳ Waiting for potential Cloudflare challenge to resolve...")
            time.sleep(5)

            # Wait for key content to render
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                        "h1, div#jobDescriptionText, div[class*='jobsearch-JobInfoHeader']"))
                )
            except Exception:
                print("  ⚠️ Selenium wait timeout, continuing with whatever loaded...")

            time.sleep(3)

            job_data = self._empty_result(url)
            job_data['url'] = driver.current_url

            # --- Title ---
            title_selectors = [
                "h1.jobsearch-JobInfoHeader-title",
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
            ]
            for sel in desc_selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, sel)
                    if elem.text.strip() and len(elem.text.strip()) > 50:
                        job_data['description'] = elem.text.strip()
                        break
                except Exception:
                    continue

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
        """Check if a scraping result has meaningful data."""
        has_title = result.get('title', '').strip() not in ('', 'Unknown Job Title')
        has_desc = (
            result.get('description', '').strip() not in ('', 'No description available')
            and len(result.get('description', '')) > 50
        )
        return has_title or has_desc