from src.scrapers.base_scraper import BaseScraper
import json
import re
import requests
import cloudscraper
from bs4 import BeautifulSoup


class NaukriScraper(BaseScraper):
    """Scraper for Naukri.com job postings — multi-tier extraction.

    Tier 1: Cloudscraper session → Naukri internal API (v4)
    Tier 2: Cloudscraper HTML → og/meta tags + embedded script data
    Tier 3: Selenium headless Chrome → fully rendered React DOM
    """

    # ------------------------------------------------------------------ #
    #  Public entry point
    # ------------------------------------------------------------------ #
    def scrape(self, url):
        """Scrape Naukri job posting using a three-tier strategy."""
        print("🔗 Scraping Naukri job posting...")

        if 'naukri.com' not in url:
            raise Exception("Invalid Naukri URL")

        # Extract job ID from URL (last 10-15 digit number)
        job_id = self._extract_job_id(url)
        print(f"📋 Extracted job ID: {job_id or 'N/A'}")

        # ---------- Tier 1: Cloudscraper + API ----------
        try:
            print("🔄 [Tier 1] Trying cloudscraper + API...")
            result = self._scrape_via_api(url, job_id)
            if self._is_valid_result(result):
                print("✅ [Tier 1] API scraping successful")
                return self._enrich_from_url(result, url)
            else:
                print("⚠️ [Tier 1] API returned incomplete data, trying next tier...")
        except Exception as e:
            print(f"❌ [Tier 1] API failed: {e}")

        # ---------- Tier 2: Cloudscraper HTML + meta/script tags ----------
        try:
            print("🔄 [Tier 2] Trying cloudscraper HTML scraping...")
            result = self._scrape_via_html(url, job_id)
            if self._is_valid_result(result):
                print("✅ [Tier 2] HTML scraping successful")
                return self._enrich_from_url(result, url)
            else:
                print("⚠️ [Tier 2] HTML scraping returned incomplete data, trying Selenium...")
        except Exception as e:
            print(f"❌ [Tier 2] HTML scraping failed: {e}")

        last_error = ""
        # ---------- Tier 3: Selenium fallback ----------
        try:
            print("🔄 [Tier 3] Trying Selenium fallback...")
            result = self._scrape_via_selenium(url)
            if self._is_valid_result(result):
                print("✅ [Tier 3] Selenium scraping successful")
                return self._enrich_from_url(result, url)
            else:
                print("⚠️ [Tier 3] Selenium returned incomplete data")
                return self._enrich_from_url(result, url)
        except Exception as e:
            last_error = str(e)
            print(f"❌ [Tier 3] Selenium failed: {e}")

        # ---------- All tiers failed — use URL parsing as last resort ----------
        print("⚠️ All network methods failed. Extracting info from URL slug...")
        msg = f"Could not scrape this job. Please paste the job description manually using the Text tab.\n\n[Render Debug]: {last_error}"
        result = self._error_result(url, msg)
        return self._enrich_from_url(result, url)

    # ------------------------------------------------------------------ #
    #  Tier 1 — Cloudscraper session + Naukri API
    # ------------------------------------------------------------------ #
    def _scrape_via_api(self, url, job_id):
        """Hit Naukri's internal jobapi/v4 using a cloudscraper session."""
        if not job_id:
            raise Exception("Could not extract job ID from URL")

        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )

        # Visit the page first to establish cookies
        page_resp = scraper.get(url, timeout=15)
        print(f"  Page status: {page_resp.status_code}")

        # Now hit the API with the session cookies
        api_url = f'https://www.naukri.com/jobapi/v4/job/{job_id}'
        api_headers = {
            'Accept': 'application/json',
            'appid': '109',
            'systemid': 'Naukri',
        }
        api_resp = scraper.get(api_url, headers=api_headers, timeout=10)
        print(f"  API status: {api_resp.status_code}")

        if api_resp.status_code != 200:
            raise Exception(f"API returned {api_resp.status_code}: {api_resp.text[:200]}")

        data = api_resp.json()
        return self._parse_api_response(data, url)

    def _parse_api_response(self, data, url):
        """Parse Naukri API v4 JSON response into job_data dict."""
        job_data = self._empty_result(url)

        # The API can return data in different structures
        # Try jobDetails first, then root level
        jd = data.get('jobDetails', data)

        # Title
        job_data['title'] = (
            jd.get('title') or
            jd.get('jobTitle') or
            jd.get('designation') or
            'Unknown Job Title'
        )

        # Description
        raw_desc = jd.get('description') or jd.get('jobDescription') or ''
        if raw_desc:
            job_data['description'] = BeautifulSoup(raw_desc, "html.parser").get_text(separator="\n").strip()

        # Company
        org = jd.get('hiringOrganization', {})
        if isinstance(org, dict):
            job_data['company'] = org.get('name', '') or jd.get('companyName', 'Unknown Company')
            same_as = org.get('sameAs', '')
            if same_as:
                job_data['company_domain'] = self.extract_domain_from_url(same_as)
        else:
            job_data['company'] = jd.get('companyName', 'Unknown Company')

        # Location
        loc = jd.get('jobLocation', {})
        if isinstance(loc, dict):
            addr = loc.get('address', {})
            if isinstance(addr, dict):
                city = addr.get('addressLocality', '')
                region = addr.get('addressRegion', '')
                job_data['location'] = f"{city}, {region}".strip(', ') or 'Not Specified'
        if job_data['location'] == 'Not Specified':
            job_data['location'] = jd.get('placeholders', {}).get('location', '') or jd.get('location', 'Not Specified')

        # Salary
        salary_data = jd.get('baseSalary', {})
        if isinstance(salary_data, dict):
            val = salary_data.get('value', {})
            if isinstance(val, dict):
                job_data['salary'] = f"{val.get('minValue', '')} - {val.get('maxValue', '')} {val.get('unitText', '')}".strip()
        if not job_data['salary']:
            job_data['salary'] = jd.get('salary', jd.get('salaryDetail', ''))

        # Experience
        job_data['experience_level'] = jd.get('experience', '')

        return job_data

    # ------------------------------------------------------------------ #
    #  Tier 2 — Cloudscraper HTML + meta tags / embedded data
    # ------------------------------------------------------------------ #
    def _scrape_via_html(self, url, job_id):
        """Scrape from Naukri HTML using meta tags, JSON-LD, and embedded script data."""
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )

        resp = scraper.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')

        job_data = self._empty_result(url)

        # --- Strategy A: JSON-LD structured data ---
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
                                job_data['salary'] = f"{val.get('minValue', '')} - {val.get('maxValue', '')} {val.get('unitText', '')}"
                    break
            except Exception:
                continue

        # --- Strategy B: og:title / og:description meta tags ---
        if job_data['title'] == 'Unknown Job Title':
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                job_data['title'] = og_title['content'].strip()

        if job_data['description'] == 'No description available':
            og_desc = soup.find('meta', property='og:description')
            if og_desc and og_desc.get('content'):
                job_data['description'] = og_desc['content'].strip()

        # --- Strategy C: Embedded preloadState in scripts ---
        if job_data['description'] == 'No description available':
            for script in soup.find_all('script'):
                if script.string and 'jobDetailsResp' in script.string:
                    try:
                        # Find the JSON blob containing job data
                        match = re.search(r'"jobDetailsResp"\s*:\s*(\{.*?\})\s*,\s*"', script.string)
                        if match:
                            embedded = json.loads(match.group(1))
                            if embedded.get('data'):
                                return self._parse_api_response(embedded['data'], url)
                    except Exception:
                        pass

        # --- Strategy D: HTML selector fallbacks ---
        if job_data['title'] == 'Unknown Job Title':
            title_selectors = [
                "h1.jd-header-title",
                "h1.styles_jd-header-title__rZwBl",
                "h1[class*='header-title']",
                "h1",
            ]
            for sel in title_selectors:
                elem = soup.select_one(sel)
                if elem and elem.get_text().strip():
                    job_data['title'] = elem.get_text().strip()
                    break

        if job_data['company'] == 'Unknown Company':
            company_selectors = [
                "a.comp-name",
                "div.jd-header-comp-name a",
                "a[class*='comp-name']",
                "div[class*='comp-name']",
            ]
            for sel in company_selectors:
                elem = soup.select_one(sel)
                if elem and elem.get_text().strip():
                    job_data['company'] = elem.get_text().strip()
                    break

        if job_data['description'] == 'No description available':
            desc_selectors = [
                "section.job-desc",
                "div.dang-inner-html",
                "div[class*='job-desc']",
                "div[class*='description']",
            ]
            for sel in desc_selectors:
                elem = soup.select_one(sel)
                if elem and elem.get_text().strip():
                    job_data['description'] = elem.get_text(separator="\n").strip()
                    break

        return job_data

    # ------------------------------------------------------------------ #
    #  Tier 3 — Selenium fallback (renders the React SPA)
    # ------------------------------------------------------------------ #
    def _scrape_via_selenium(self, url):
        """Use headless Chrome to render the Naukri SPA and extract content."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time

        driver = None
        try:
            driver = self.init_selenium_driver()
            driver.get(url)

            # Wait for key content to render
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                        "h1, [class*='jd-header-title'], [class*='job-title'], [class*='comp-name']"))
                )
            except Exception:
                print("  ⚠️ Selenium wait timeout, continuing with whatever loaded...")

            # Give React a moment to finish rendering
            time.sleep(3)

            job_data = self._empty_result(url)
            job_data['url'] = driver.current_url

            # --- Title ---
            title_selectors = [
                "h1.jd-header-title",
                "h1[class*='header-title']",
                "h1[class*='job-title']",
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
                "a[class*='comp-name']",
                "div[class*='comp-name'] a",
                "a.comp-name",
                "div.jd-header-comp-name a",
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
                "span[class*='location']",
                "div[class*='location']",
                "a[class*='location']",
            ]
            for sel in location_selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, sel)
                    if elem.text.strip():
                        job_data['location'] = elem.text.strip()
                        break
                except Exception:
                    continue

            # --- Experience ---
            experience_selectors = [
                "span[class*='experience']",
                "div[class*='experience']",
            ]
            for sel in experience_selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, sel)
                    if elem.text.strip():
                        job_data['experience_level'] = elem.text.strip()
                        break
                except Exception:
                    continue

            # --- Salary ---
            salary_selectors = [
                "span[class*='salary']",
                "div[class*='salary']",
            ]
            for sel in salary_selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, sel)
                    if elem.text.strip():
                        job_data['salary'] = elem.text.strip()
                        break
                except Exception:
                    continue

            # --- Description ---
            desc_selectors = [
                "section.job-desc",
                "div.dang-inner-html",
                "div[class*='job-desc']",
                "div[class*='description']",
                "div[class*='jd-desc']",
            ]
            for sel in desc_selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, sel)
                    if elem.text.strip() and len(elem.text.strip()) > 50:
                        job_data['description'] = elem.text.strip()
                        break
                except Exception:
                    continue

            # If we still have no description, try to get the full page text from the main content area
            if job_data['description'] == 'No description available':
                try:
                    main = driver.find_element(By.CSS_SELECTOR, "main, #root, [class*='job-detail']")
                    text = main.text.strip()
                    if len(text) > 200:
                        job_data['description'] = text
                except Exception:
                    pass

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
        """Extract the numeric job ID from a Naukri URL."""
        # Naukri URLs end with a long numeric ID like -020326030847
        match = re.search(r'-(\d{10,15})(?:\?|$|/)', url.rstrip('/') + '/')
        return match.group(1) if match else None

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
            'experience_level': '',
            'salary': '',
            'company_profile': '',
            'job_portal': 'naukri.com',
            'url': url,
        }

    def _error_result(self, url, message):
        """Return an error result with guidance for the user."""
        result = self._empty_result(url)
        result['description'] = message
        result['error'] = message
        return result

    def _is_valid_result(self, result):
        """Check if a scraping result has meaningful data."""
        has_title = result.get('title', '').strip() not in ('', 'Unknown Job Title')
        has_desc = result.get('description', '').strip() not in ('', 'No description available')
        # Consider valid if we got either a real title or a real description
        return has_title or has_desc

    def _parse_url_slug(self, url):
        """Extract job title, company, and location from Naukri URL slug.

        Naukri URLs follow the pattern:
          /job-listings-{title}-{company}-{location}-{experience}-{id}
        Example:
          /job-listings-python-developer-indiafilings-chennai-0-to-3-years-020326030847
        """
        info = {'title': '', 'company': '', 'location': ''}

        try:
            from urllib.parse import urlparse
            path = urlparse(url).path.rstrip('/')

            # Remove the prefix and job ID suffix
            slug = re.sub(r'^/job-listings-', '', path)
            slug = re.sub(r'-\d{10,15}$', '', slug)

            if not slug:
                return info

            # Remove experience suffix like "0-to-3-years"
            slug = re.sub(r'-\d+-to-\d+-years?$', '', slug)

            # Known Indian cities for location detection
            cities = {
                'mumbai', 'delhi', 'bangalore', 'bengaluru', 'chennai', 'hyderabad',
                'pune', 'kolkata', 'ahmedabad', 'jaipur', 'noida', 'gurgaon',
                'gurugram', 'ghaziabad', 'lucknow', 'chandigarh', 'indore',
                'coimbatore', 'kochi', 'nagpur', 'bhopal', 'mysore', 'thiruvananthapuram',
                'delhi-ncr', 'new-delhi', 'navi-mumbai', 'greater-noida',
                'remote', 'work-from-home', 'india',
            }

            parts = slug.split('-')

            # Try to find city by scanning from the end
            location_parts = []
            remaining = list(parts)  # copy
            for i in range(len(parts) - 1, -1, -1):
                candidate = '-'.join(parts[i:])
                if candidate.lower() in cities:
                    location_parts = parts[i:]
                    remaining = parts[:i]
                    break
                # Also check single word
                if parts[i].lower() in cities:
                    location_parts = [parts[i]]
                    remaining = parts[:i]
                    break

            if location_parts:
                info['location'] = ' '.join(w.capitalize() for w in location_parts)

            # Now split remaining into title and company
            # Heuristic: company is usually the last 1-3 words before location,
            # and title is everything before that.
            if remaining:
                # Common company suffixes that help identify boundaries
                company_indicators = {
                    'private', 'limited', 'ltd', 'pvt', 'inc', 'corp', 'llp',
                    'technologies', 'solutions', 'systems', 'services',
                    'software', 'infotech', 'consulting', 'labs',
                }

                # Try to find where the company name starts
                company_start = None
                for i in range(len(remaining) - 1, max(0, len(remaining) - 5), -1):
                    if remaining[i].lower() in company_indicators:
                        # Likely part of company name — scan backwards a bit more
                        company_start = max(0, i - 2)
                        break

                if company_start is not None and company_start > 0:
                    info['title'] = ' '.join(w.capitalize() for w in remaining[:company_start])
                    info['company'] = ' '.join(w.capitalize() for w in remaining[company_start:])
                elif len(remaining) >= 3:
                    # Guess: last word/segment is company, rest is title
                    # Try splitting at the last naturally-capitalizable segment
                    info['title'] = ' '.join(w.capitalize() for w in remaining[:-1])
                    info['company'] = remaining[-1].capitalize()
                else:
                    info['title'] = ' '.join(w.capitalize() for w in remaining)

        except Exception:
            pass

        return info

    def _enrich_from_url(self, result, url):
        """Fill in missing fields using data extracted from the URL slug."""
        url_info = self._parse_url_slug(url)

        if result.get('title') in ('', 'Unknown Job Title') and url_info['title']:
            result['title'] = url_info['title']
            print(f"  📎 Title from URL: {url_info['title']}")

        if result.get('company') in ('', 'Unknown Company') and url_info['company']:
            result['company'] = url_info['company']
            print(f"  📎 Company from URL: {url_info['company']}")

        if result.get('location') in ('', 'Not Specified') and url_info['location']:
            result['location'] = url_info['location']
            print(f"  📎 Location from URL: {url_info['location']}")

        return result
