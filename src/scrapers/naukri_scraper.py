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
        """Multi-layer scraping strategy for Naukri (v2.2 Resilience Update)."""
        print("🔗 Scraping Naukri job posting...")

        if 'naukri.com' not in url:
            raise Exception("Invalid Naukri URL")

        # Extract job ID from URL
        job_id = self._extract_job_id(url)
        print(f"📋 Extracted job ID: {job_id or 'N/A'}")

        # ---------- Tier 1: API (Fastest/Strongest) ----------
        try:
            print("🔄 [Tier 1] Trying Direct API (Mobile/H2)...")
            result = self._scrape_via_api(url, job_id)
            if self._is_valid_result(result):
                print("✅ [Tier 1] API scraping successful")
                return self._enrich_from_url(result, url)
        except Exception as e:
            print(f"❌ [Tier 1] API failed: {e}")

        # ---------- Tier 1.5: Google Cache Fallback ----------
        try:
            cache_result = self._scrape_via_google_cache(url, job_id)
            if cache_result and self._is_valid_result(cache_result):
                print("✅ [Tier 1.5] Google Cache scraping successful")
                return self._enrich_from_url(cache_result, url)
        except Exception as e:
            print(f"❌ [Tier 1.5] Google Cache failed: {e}")

        # ---------- Tier 2: Cloudscraper HTML ----------
        try:
            print("🔄 [Tier 2] Trying Cloudscraper HTML + Density-Scan...")
            result = self._scrape_via_html(url, job_id)
            if self._is_valid_result(result):
                print("✅ [Tier 2] HTML scraping successful")
                return self._enrich_from_url(result, url)
        except Exception as e:
            print(f"❌ [Tier 2] HTML scraping failed: {e}")

        # ---------- Tier 3: Selenium fallback ----------
        last_error = "Unknown Error"
        try:
            print("🔄 [Tier 3] Trying Selenium fallback...")
            result = self._scrape_via_selenium(url)
            if self._is_valid_result(result):
                print("✅ [Tier 3] Selenium scraping successful")
                return self._enrich_from_url(result, url)
            else:
                last_error = "Selenium returned incomplete data"
        except Exception as e:
            last_error = str(e)
            print(f"❌ [Tier 3] Selenium failed: {e}")

        # ---------- Tier 3.5: Search Snippet Fallback (New) ----------
        try:
            print("🔄 [Tier 3.5] Trying Search Snippet Fallback...")
            slug_info = self._parse_url_slug(url)
            search_res = self._search_snippet_fallback(url, slug_info['title'], slug_info['company'])
            
            if search_res and search_res.get('description'):
                result = self._empty_result(url)
                # ALWAYS use slug-parsed title/company — they come from Naukri's own URL
                # Search results can be unrelated pages (e.g., Google policy pages)
                result['title'] = slug_info['title']
                result['company'] = slug_info['company']
                result['location'] = slug_info['location']
                result['description'] = search_res['description']
                print(f"✅ [Tier 3.5] Search description found. Slug title: {result['title']}")
                return result
        except Exception as e:
            print(f"❌ [Tier 3.5] Search fallback failed: {e}")

        # ---------- Tier 4: Smart Slug Recovery (Always succeeds) ----------
        print("⚠️ All network methods failed. Running Smart Slug recovery...")
        result = self._empty_result(url)
        return self._smart_slug_recovery(result, url, last_error=last_error)

    # ------------------------------------------------------------------ #
    #  Tier 1 — Cloudscraper session + Naukri API
    # ------------------------------------------------------------------ #
    def _scrape_via_api(self, url, job_id):
        """Hit Naukri's internal jobapi using v4/v3 and the Direct Mobile API with H2 support."""
        if not job_id:
            raise Exception("Could not extract job ID from URL")

        # Profiles to try: v4 Web API, Android App Emulation, and Googlebot Cache
        profiles = [
            {'name': 'Android App API', 'url': f"https://www.naukri.com/jobapi/v4/job/{job_id}?microsite=y", 'ua': 'Naukri/1.0 (Android 11; Pixel 5)', 'h2': True, 'app': True},
            {'name': 'Web v4 API (appid:121)', 'url': f"https://www.naukri.com/jobapi/v4/job/{job_id}?microsite=y", 'ua': self.headers.get('User-Agent'), 'h2': True, 'app': False},
            {'name': 'Web v4 API (appid:109)', 'url': f"https://www.naukri.com/jobapi/v4/job/{job_id}?microsite=y", 'ua': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36', 'h2': True, 'app': False},
        ]

        for profile in profiles:
            try:
                print(f"🔄 [Tier 1] Querying {profile['name']}...")
                
                resp = None
                # Use httpx for H2 if requested (High success rate for API.naukri.com)
                if profile.get('h2'):
                    try:
                        import httpx
                        client = httpx.Client(http2=True, timeout=12)
                        headers = {
                            'User-Agent': profile['ua'],
                            'client_id': 'd369c73d-82d8-4f51-b8f4-6f0925c34537',
                            'appid': '109' if profile.get('app') else ('121' if '121' in profile['name'] else '109'),
                            'systemid': 'Naukri' if profile.get('app') else ('121' if '121' in profile['name'] else '109'),
                            'X-Requested-With': 'com.naukri.android' if profile.get('app') else None,
                            'Accept': 'application/json',
                            'Referer': 'https://www.naukri.com/',
                            'Cache-Control': 'no-cache'
                        }
                        # Remove None values
                        headers = {k: v for k, v in headers.items() if v is not None}
                        
                        resp = client.get(profile['url'], headers=headers)
                        print(f"  📡 [Tier 1] {profile['name']} Status: {resp.status_code}")
                        
                        if resp.status_code == 200:
                            job_data = self._parse_api_response(resp.json(), url)
                            if self._is_valid_result(job_data):
                                print(f"✅ [Tier 1] {profile['name']} successful")
                                return job_data
                        client.close()
                    except Exception as h2_err:
                        print(f"  ⚠️ [Tier 1] H2 Client failed: {h2_err}")
                
                # Fallback to cloudscraper
                scraper = cloudscraper.create_scraper(
                    interpreter='nodejs',
                    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
                )
                scraper.headers.update({
                    'User-Agent': profile['ua'],
                    'Referer': 'https://www.google.com/'
                })
                
                # Try multiple appid/systemid combinations (Rotating Headers)
                auth_profiles = [
                    {'appid': '121', 'systemid': '121', 'client_id': 'd369c73d-82d8-4f51-b8f4-6f0925c34537'},
                    {'appid': '109', 'systemid': 'Naukri', 'client_id': 'd369c73d-82d8-4f51-b8f4-6f0925c34537'},
                ]
                
                success = False
                for auth in auth_profiles:
                    if 'api.naukri.com' in profile['url'] or 'jobapi' in profile['url']:
                        scraper.headers.update(auth)
                    
                    resp = scraper.get(profile['url'], timeout=12)
                    if resp.status_code == 200:
                        job_data = self._parse_api_response(resp.json(), url)
                        if self.validate_job_data(job_data):
                            print(f"✅ [Tier 1] {profile['name']} successful with appid={auth['appid']}")
                            return job_data
                    elif resp.status_code == 403:
                        continue # Try next auth profile
                    else:
                        print(f"  ⚠️ {profile['name']} status {resp.status_code} for appid={auth['appid']}")
            except Exception as e:
                print(f"  ⚠️ {profile['name']} error: {str(e)}")

        raise Exception("Bulk API extraction failed (All profiles)")

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
            job_data['company'] = org.get('name', '') or jd.get('companyName', jd.get('company', 'Unknown Company'))
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
            job_data['location'] = jd.get('placeholders', {}).get('location', '') or jd.get('location', jd.get('jobLocation', 'Not Specified'))
            if isinstance(job_data['location'], dict): # Handle object location
                job_data['location'] = job_data['location'].get('label', 'Not Specified')

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
        """Scrape from Naukri HTML using Node.js interpreter bypass and Search Referer."""
        profiles = [
            {'name': 'Browser (Chrome)', 'ua': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36'},
            {'name': 'Googlebot', 'ua': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}
        ]
        
        last_exception = None
        for profile in profiles:
            try:
                print(f"🔄 [Tier 2] Fetching HTML as {profile['name']} (Node.js Bypass)...")
                scraper = cloudscraper.create_scraper(
                    interpreter='nodejs',
                    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
                )
                scraper.headers.update({
                    'User-Agent': profile['ua'],
                    'Referer': 'https://www.google.com/',
                    'X-Requested-With': 'com.naukri.naukri'
                })
                
                # Handshake via Google
                if profile['name'] == 'Browser (Chrome)':
                    scraper.get("https://www.google.com/url?q=https://www.naukri.com/", timeout=8)
                
                resp = scraper.get(url, timeout=15)
                if resp.status_code == 200:
                    # Try Next.js hydration parse FIRST (most complete)
                    hydrated = self._parse_next_js_hydration(resp.text, url)
                    if hydrated: # Even if partial, it's often better than nothing
                        print(f"✅ [Tier 2] Next.js hydration extraction successful with {profile['name']}")
                        return hydrated
                    
                    # Fallback to standard density-scan / meta tags
                    job_data = self._parse_html_content(resp.content, url)
                    if self.validate_job_data(job_data):
                        print(f"✅ [Tier 2] HTML extraction successful with {profile['name']}")
                        return job_data
                else:
                    print(f"  ⚠️ HTML fetch status {resp.status_code} for {profile['name']}")
            except Exception as e:
                print(f"  ⚠️ HTML fetch error for {profile['name']}: {str(e)}")
                last_exception = e
                
        if last_exception: raise last_exception
        raise Exception("HTML scraping failed for all profiles")

    def _parse_html_content(self, html_content, url):
        """Parse the HTML content using multiple strategies."""
        soup = BeautifulSoup(html_content, 'html.parser')
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

        # --- Strategy D: window.__PRELOADED_STATE__ (Internal State) ---
        if job_data['description'] == 'No description available':
            try:
                for script in soup.find_all('script'):
                    content = script.string
                    if content and 'window.__PRELOADED_STATE__' in content:
                        match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*(\{.*?\})(?:;|$)', content, re.DOTALL)
                        if match:
                            try:
                                state_json = json.loads(match.group(1))
                                # Deep search for 'description' or 'jobDescription'
                                def find_recursive(obj, key):
                                    if isinstance(obj, dict):
                                        if key in obj: return obj[key]
                                        for v in obj.values():
                                            res = find_recursive(v, key)
                                            if res: return res
                                    elif isinstance(obj, list):
                                        for it in obj:
                                            res = find_recursive(it, key)
                                            if res: return res
                                    return None

                                desc = find_recursive(state_json, 'jobDescription') or find_recursive(state_json, 'description')
                                if desc and len(str(desc)) > 100:
                                    print("✅ [Tier 2] window.__PRELOADED_STATE__ extraction successful")
                                    job_data['description'] = BeautifulSoup(str(desc), "html.parser").get_text(separator="\n").strip()
                                    if self.validate_job_data(job_data): return job_data
                            except: pass

                # --- Strategy E: Density-Based Balanced JSON Scan ---
                for script in soup.find_all('script'):
                    content = script.string
                    if content and 'jobDescription' in content:
                        indices = [m.start() for m in re.finditer('jobDescription', content)]
                        for idx in indices:
                            start_node = content.rfind('{', 0, idx)
                            if start_node == -1: continue
                            
                            stack = []
                            for i in range(start_node, len(content)):
                                if content[i] == '{': stack.append('{')
                                elif content[i] == '}':
                                    if stack: stack.pop()
                                    if not stack:
                                        try:
                                            jd_block = json.loads(content[start_node:i+1])
                                            if jd_block.get('jobDescription') or jd_block.get('description'):
                                                print("✅ [Tier 2] Balanced Density JSON extraction successful")
                                                parsed = self._parse_api_response(jd_block, url)
                                                if self.validate_job_data(parsed): return parsed
                                        except: pass
                                        break
            except Exception: pass

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
        max_retries = 2
        last_exception = None

        for attempt in range(max_retries):
            try:
                driver = self.init_selenium_driver()
                
                # Add a bit of jitter and longer initial timeout
                driver.set_page_load_timeout(45)
                driver.get(url)
                
                # CRITICAL: Wait for Cloudflare/antibot JS challenge to resolve
                print(f"  ⏳ Waiting for potential Cloudflare challenge to resolve (Attempt {attempt+1})...")
                time.sleep(18) # Maximum for Render stability
                
                # Check if we're still on a challenge page
                try:
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    if "Checking your browser" in page_text or "Verification is taking longer" in page_text:
                        print("  🕒 Cloudflare challenge persistent, waiting another 10s...")
                        time.sleep(10)
                except Exception: pass

                # Trigger React lazy loading by scrolling
                driver.execute_script("window.scrollTo(0, 500);")
                time.sleep(2)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                driver.execute_script("window.scrollTo(0, 0);") 
                time.sleep(1)

                # Wait for key content to render - be more inclusive
                job_data = self._empty_result(url)
                job_data['url'] = driver.current_url

                try:
                    WebDriverWait(driver, 35).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR,
                            "h1, [class*='jd-header-title'], [class*='job-title'], [class*='comp-name'], main"))
                    )
                except Exception:
                    print(f"  ⚠️ Selenium wait timeout on attempt {attempt+1}. Running 'Last Ghasp' capture...")
                    # Even if it times out, grab whatever is in the body
                    try:
                        raw_body = driver.find_element(By.TAG_NAME, "body").text
                        if len(raw_body) > 300:
                            # Try Density-Scan on raw body text (might be JSON-LD in body)
                            if 'jobDescription' in raw_body:
                                match = re.search(r'(\{.*?"jobDescription".*?\})', raw_body)
                                if match:
                                    try:
                                        jd_block = json.loads(match.group(1))
                                        job_data = self._parse_api_response(jd_block, url)
                                        if self.validate_job_data(job_data):
                                            print("✅ [Tier 3] 'Last Ghasp' Density capture successful")
                                            return job_data
                                    except: pass
                    except: pass

                # Give React a moment to finish rendering
                time.sleep(4)
                job_data['url'] = driver.current_url

                # --- Title ---
                title_selectors = [
                    "h1[class*='styles_jd-header-title']",
                    "h1.styles_jd-header-title",
                    "h1.jd-header-title", 
                    "h1[class*='header-title']", 
                    "h1[class*='job-title']", 
                    "h1"
                ]
                for sel in title_selectors:
                    try:
                        elem = driver.find_element(By.CSS_SELECTOR, sel)
                        if elem.text.strip():
                            job_data['title'] = elem.text.strip()
                            break
                    except Exception: continue

                # --- Company ---
                company_selectors = [
                    "a[class*='styles_jd-header-comp-name']",
                    "a[class*='styles_jhc__hiring-for']",
                    "a.styles_jd-header-comp-name",
                    "div[class*='styles_jd-header-comp-name']",
                    "a[title*='Careers']",
                    "a[class*='comp-name']", 
                    "div[class*='comp-name'] a", 
                    "a.comp-name", 
                    "div.jd-header-comp-name a"
                ]
                for sel in company_selectors:
                    try:
                        elem = driver.find_element(By.CSS_SELECTOR, sel)
                        if elem.text.strip():
                            job_data['company'] = elem.text.strip()
                            break
                    except Exception: continue

                # --- Location ---
                location_selectors = [
                    "span[class*='styles_jlc__location']",
                    "span[class*='styles_jhc__location']",
                    "span.styles_jlc__location",
                    "span.styles_jhc__location",
                    ".location a",
                    "span[class*='location']", 
                    "div[class*='location']", 
                    "a[class*='location']"
                ]
                for sel in location_selectors:
                    try:
                        elem = driver.find_element(By.CSS_SELECTOR, sel)
                        if elem.text.strip():
                            job_data['location'] = elem.text.strip()
                            break
                    except Exception: continue

                # --- Experience ---
                experience_selectors = [
                    "span[class*='styles_jhc__exp']",
                    "span.styles_jhc__exp",
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
                    "span[class*='styles_jhc__salary']",
                    "span.styles_jhc__salary",
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
                # First try to click "Read more" if present
                try:
                    read_more_selectors = [
                        "span.styles_read-more__6_P_x",
                        "span[class*='styles_read-more']",
                        "a[class*='read-more']",
                        "button[class*='read-more']"
                    ]
                    for rm_sel in read_more_selectors:
                        try:
                            rm_btn = driver.find_element(By.CSS_SELECTOR, rm_sel)
                            if rm_btn.is_displayed():
                                print(f"  👆 Clicking 'Read more' button ({rm_sel})...")
                                driver.execute_script("arguments[0].click();", rm_btn)
                                time.sleep(2)
                                break
                        except: continue
                except Exception as e:
                    print(f"  ⚠️ Read more click failed: {e}")

                desc_selectors = [
                    "section[class*='styles_job-description']",
                    "section[class*='styles_job-desc-container']",
                    "div[class*='styles_job-desc-container']",
                    "div[class*='styles_jd-description']",
                    "section.job-desc", 
                    "section[class*='job-desc']",
                    "div.dang-inner-html", 
                    "div[class*='job-desc']", 
                    "div[class*='description']", 
                    "div[class*='jd-desc']"
                ]
                for sel in desc_selectors:
                    try:
                        elem = driver.find_element(By.CSS_SELECTOR, sel)
                        if elem.text.strip() and len(elem.text.strip()) > 50:
                            job_data['description'] = elem.text.strip()
                            break
                    except Exception: continue

                # --- Text-based Fallback for Description ---
                if job_data['description'] == 'No description available':
                    try:
                        # Try to find the section by text if selectors failed
                        body_content = driver.find_element(By.TAG_NAME, "body")
                        text = body_content.text
                        
                        # Debug: Log first 200 chars of body text to see if it's a splash screen
                        preview = text[:200].replace('\n', ' ') if len(text) > 200 else text.replace('\n', ' ')
                        print(f"  📝 Body text preview: {preview}...")

                        # Stage 0: Look for Next.js hydration data in source if UI hasn't rendered
                        if len(text) < 500:
                            print("  🔍 Body text too short, attempting Next.js hydration parse from source...")
                            source = driver.page_source
                            hydrated_data = self._parse_next_js_hydration(source, url)
                            if hydrated_data and self._is_valid_result(hydrated_data):
                                return hydrated_data

                        # Stage 1: Last Ghasp field recovery
                        # Title
                        if job_data['title'] == 'Unknown Job Title':
                            lines = text.split("\n")
                            for line in lines[:5]: # Check first 5 lines for title
                                if len(line.strip()) > 10 and len(line.strip()) < 100:
                                    job_data['title'] = line.strip()
                                    break
                        
                        # Company
                        if job_data['company'] == 'Unknown Company':
                            match = re.search(r'About\s+(.*?)\s+', text, re.I)
                            if match: job_data['company'] = match.group(1).strip()

                        # Description Search
                        headings = ["Job description", "Job Overview", "About the job", "Roles and Responsibilities"]
                        for heading in headings:
                            if heading.lower() in text.lower():
                                # Case insensitive split
                                pattern = re.compile(re.escape(heading), re.IGNORECASE)
                                parts = pattern.split(text, 1)
                                if len(parts) > 1:
                                    potential_desc = parts[1].split("Role", 1)[0].split("About Company", 1)[0].strip()
                                    if len(potential_desc) > 150:
                                        job_data['description'] = potential_desc
                                        break
                        
                        # Stage 2: If still missing description, look for ANY large text block (>200 chars)
                        if job_data['description'] == 'No description available':
                            paragraphs = text.split("\n\n")
                            best_p = max(paragraphs, key=len, default="")
                            if len(best_p) > 200:
                                job_data['description'] = best_p.strip()
                    except Exception: pass

                # Cleanup description: remove Naukri fraud alert boilerplate
                if job_data['description'] and 'Beware of imposters' in job_data['description']:
                    boilerplate_patterns = [
                        r'Beware of imposters!.*?\.\.\.Read more',
                        r'Naukri\.com does not promise.*?money\.',
                        r'Fraudsters may ask you to pay.*?Fee',
                    ]
                    for pattern in boilerplate_patterns:
                        job_data['description'] = re.sub(pattern, '', job_data['description'], flags=re.DOTALL).strip()

                if job_data['title'] != 'Unknown Job Title' or job_data['description'] != 'No description available':
                    return job_data
                
                # Save debug HTML on failure
                try:
                    with open("debug_naukri_page.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    print("  📄 Debug page source saved to debug_naukri_page.html")
                except: pass
                
                raise Exception("Page loaded but no content found")

            except Exception as e:
                last_exception = e
                print(f"  ❌ Selenium attempt {attempt+1} failed: {str(e)}")
            finally:
                if driver:
                    try:
                        driver.quit()
                    except Exception: pass

        raise last_exception or Exception("Selenium scraping failed after retries")

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
        result['title'] = 'Extraction Failed'
        result['company'] = 'Extraction Failed'
        result['location'] = 'Extraction Failed'
        result['description'] = message
        result['error'] = message
        return result


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

            # Use the clean path (no query params) to extract the slug
            slug = path.split("job-listings-")[-1]
            parts = slug.split('-')

            # Comprehensive list of major Indian cities found in Naukri URLs
            cities = {
                'chennai', 'bengaluru', 'bangalore', 'mumbai', 'pune', 'hyderabad', 'gurgaon', 'noida',
                'delhi', 'new-delhi', 'kolkata', 'ahmedabad', 'surat', 'jaipur', 'lucknow', 'kanpur',
                'nagpur', 'indore', 'thane', 'bhopal', 'visakhapatnam', 'vadodara', 'patna',
                'ludhiana', 'agra', 'nashik', 'faridabad', 'meerut', 'rajkot', 'kalyan', 'vasai-virar',
                'varanasi', 'srinagar', 'aurangabad', 'dhanbad', 'amritsar', 'navi-mumbai', 'allahabad',
                'howrah', 'ranchi', 'gwalior', 'jabalpur', 'coimbatore', 'vijayawada', 'madurai', 'guwahati',
                'chandigarh', 'hubli', 'amravati', 'jodhpur', 'tiruchirappalli', 'tiruchirapalli',
                'bareilly', 'mysore', 'tiruppur', 'salem', 'trichy', 'kochi', 'mangalore', 'dehradun',
                'hisar', 'gurugram', 'ghaziabad', 'thiruvananthapuram', 'greater-noida',
                'remote', 'work-from-home', 'india',
            }

            # 1. Strip trailing job ID (long digit string)
            if parts and parts[-1].isdigit() and len(parts[-1]) >= 6:
                parts.pop()

            # 2. Strip trailing experience like "0-to-1-years" or "3-to-5-years"
            #    When split by '-', this becomes ['0', 'to', '1', 'years'] (4 parts)
            import re
            tail = '-'.join(parts[-4:]) if len(parts) >= 4 else ''
            if re.match(r'^\d+-to-\d+-years?$', tail):
                parts = parts[:-4]
            else:
                tail = '-'.join(parts[-3:]) if len(parts) >= 3 else ''
                if re.match(r'^\d+-to-\d+$', tail):
                    parts = parts[:-3]

            # 2. Exhaustively strip cities from the end
            location_parts = []
            while parts and (parts[-1].lower() in cities or (len(parts) > 1 and f"{parts[-2]}-{parts[-1]}".lower() in cities)):
                # Handle multi-word cities like "New Delhi" (new-delhi)
                if len(parts) > 1 and f"{parts[-2]}-{parts[-1]}".lower() in cities:
                    location_parts.insert(0, parts.pop())
                    location_parts.insert(0, parts.pop())
                else:
                    location_parts.insert(0, parts.pop())

            if location_parts:
                info['location'] = ' '.join(w.capitalize() for w in location_parts)

            # 3. Identify Company and Title from remaining parts
            remaining = parts
            if remaining:
                company_indicators = {
                    'private', 'limited', 'ltd', 'pvt', 'inc', 'corp', 'llp',
                    'technologies', 'solutions', 'systems', 'services', 'companies',
                    'software', 'infotech', 'consulting', 'labs', 'group', 'industries',
                    'consultancy', 'advisors'
                }

                # Find the LAST occurrence of a company indicator
                indicator_idx = -1
                for i in range(len(remaining) - 1, -1, -1):
                    if remaining[i].lower() in company_indicators:
                        indicator_idx = i
                        break

                if indicator_idx != -1:
                    # Heuristic: Company usually starts 1-2 words before the indicator
                    start_idx = max(0, indicator_idx - 1)
                    if start_idx > 0 and remaining[start_idx].lower() in {'consulting', 'technologies', 'solutions'}:
                        start_idx -= 1

                    info['title'] = ' '.join(w.capitalize() for w in remaining[:start_idx])
                    info['company'] = ' '.join(w.capitalize() for w in remaining[start_idx:])
                elif len(remaining) >= 4:
                    split = len(remaining) // 2
                    info['title'] = ' '.join(w.capitalize() for w in remaining[:split])
                    info['company'] = ' '.join(w.capitalize() for w in remaining[split:])
                else:
                    info['title'] = ' '.join(w.capitalize() for w in remaining)

        except Exception as e:
            print(f"  ⚠️ Slug parsing error: {e}")

        return info

    def _enrich_from_url(self, result, url):
        """Fill in missing fields using data extracted from the URL slug."""
        url_info = self._parse_url_slug(url)

        # Allow updating even if set to "Extraction Failed"
        def should_update(current_val, placeholders):
            if not current_val: return True
            return current_val.strip() in placeholders

        placeholders = ('', 'Unknown Job Title', 'Unknown Company', 'Not Specified', 'Extraction Failed')

        if should_update(result.get('title'), placeholders) and url_info['title']:
            result['title'] = url_info['title']
            print(f"  📎 Title from URL: {url_info['title']}")

        if should_update(result.get('company'), placeholders) and url_info['company']:
            result['company'] = url_info['company']
            print(f"  📎 Company from URL: {url_info['company']}")

        if should_update(result.get('location'), placeholders) and url_info['location']:
            result['location'] = url_info['location']
            print(f"  📎 Location from URL: {url_info['location']}")

        return result

    # ------------------------------------------------------------------ #
    #  Tier 4 — Advanced Smart Slug Recovery (Final Safety Net)
    # ------------------------------------------------------------------ #
    def _smart_slug_recovery(self, job_data, url, last_error=""):
        """Extract information from the URL slug if all scraping fails."""
        try:
            # URL: https://www.naukri.com/job-listings-user-interface-designer-intern-unpaid-axagon-solutions-chennai-0-to-1-years-180326036796
            # Extract the part between job-listings- and the job-id
            parts = url.split("job-listings-")[-1].split("-")
            if parts and parts[-1].isdigit(): parts.pop() # Remove ID
            
            # De-hyphenate and capitalize
            readable = " ".join(parts).title()
            
            # Enrich from URL first (gets title/company/location specifically)
            job_data = self._enrich_from_url(job_data, url)
            
            # If title is still unknown, use de-hyphenated readable string
            if job_data['title'] == 'Unknown Job Title' or not job_data['title']:
                job_data['title'] = readable
                
            # Generate a "Summary Description"
            summary = (
                f"📝 Job Summary: {job_data['title']}\n\n"
                f"🌍 Location: {job_data['location'] or 'Chennai'}\n"
                f"🏢 Company: {job_data['company'] or 'Unknown Company'}\n\n"
                f"⚠️ Note: Full description could not be automatically extracted due to portal blocks from Render. "
                f"Please visit the official Naukri link below to see all requirements."
            )
            if last_error:
                summary += f"\n\n[Debug Info]: {last_error}"
            
            job_data['description'] = summary
            print("✅ [Tier 4] Smart Slug recovery successful")
        except Exception as e:
            print(f"  ⚠️ Smart Slug recovery failed: {str(e)}")
            
        return job_data

    # ------------------------------------------------------------------ #
    #  Tier 1.5 — Google Cache Fallback
    # ------------------------------------------------------------------ #
    def _scrape_via_google_cache(self, url, job_id):
        """Attempt to fetch the job page from Google's search cache."""
        try:
            cache_url = f"http://webcache.googleusercontent.com/search?q=cache:{url}"
            print(f"🔄 [Tier 1.5] Attempting Google Cache fetch: {cache_url}")
            
            scraper = cloudscraper.create_scraper(interpreter='nodejs')
            # Modern Googlebot-Mobile header
            scraper.headers.update({
                'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/W.X.Y.Z Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                'Referer': 'https://www.google.com/'
            })
            
            resp = scraper.get(cache_url, timeout=12)
            if resp.status_code == 200:
                print("✅ [Tier 1.5] Google Cache page fetched")
                return self._parse_html_content(resp.content, url)
        except Exception as e:
            print(f"  ⚠️ Google Cache failed: {str(e)}")
        return None

    def _parse_next_js_hydration(self, html, url):
        """Parse Next.js self.__next_f.push hydration stream for job details (v2.6 Optimized)."""
        try:
            job_data = self._empty_result(url)
            
            # Find all strings in the Next flow
            # The data is often split across multiple self.__next_f.push calls
            payloads = re.findall(r'self\.__next_f\.push\(\[.*?,(?:"|`)(.*?)(?:"|`)\]\)', html, re.DOTALL)
            
            # Handle standard script tags too (Preloaded State)
            scripts = re.findall(r'<script id="__NEXT_DATA__".*?>(.*?)</script>', html, re.DOTALL)
            payloads.extend(scripts)
            
            # Avoid over-cleaning before regex as it breaks escaped quote detection
            combined = "".join(payloads)
            if not combined: 
                print("  ⚠️ Next.js: No payloads found in source")
                return None

            # 1. Regex Strategy for Title
            try:
                for pattern in [r'"title"\s*:\s*"(.*?[^\\])"', r'"jobTitle"\s*:\s*"(.*?[^\\])"']:
                    match = re.search(pattern, combined)
                    if match: 
                        job_data['title'] = match.group(1).replace('\\"', '"').replace('\\\\', '\\').encode('utf-8').decode('unicode_escape', 'ignore')
                        break
            except Exception as e: print(f"  ⚠️ Next.js Title parse failed: {e}")
            
            # 2. Regex Strategy for Company
            try:
                for pattern in [r'"companyName"\s*:\s*"(.*?[^\\])"', r'"hiringOrganization".*?"name"\s*:\s*"(.*?[^\\])"']:
                    match = re.search(pattern, combined, re.DOTALL)
                    if match: 
                        job_data['company'] = match.group(1).replace('\\"', '"').replace('\\\\', '\\').encode('utf-8').decode('unicode_escape', 'ignore')
                        break
            except Exception as e: print(f"  ⚠️ Next.js Company parse failed: {e}")
            
            # 3. Aggressive Description Search
            try:
                # 3a. Precise Regex for Escaped JSON
                for pattern in [r'"jobDescription"\s*:\s*"(.*?(?<!\\)(?:\\\\)*)"', r'"description"\s*:\s*"(.*?(?<!\\)(?:\\\\)*)"']:
                    desc_match = re.search(pattern, combined, re.DOTALL)
                    if desc_match:
                        raw_desc = desc_match.group(1).replace('\\"', '"').replace('\\\\', '\\').replace('\\/', '/')
                        try:
                            decoded_desc = raw_desc.encode('utf-8').decode('unicode_escape', 'ignore')
                        except:
                            decoded_desc = raw_desc
                        
                        if len(decoded_desc) > 100:
                            job_data['description'] = BeautifulSoup(decoded_desc, "html.parser").get_text(separator=' ').strip()
                            break
                
                # 3b. Fallback: Take anything long and HTML-like if desc is still missing
                if len(job_data['description']) < 100:
                    potential_blocks = re.findall(r'>(.*?)<', combined)
                    best_block = max(potential_blocks, key=len, default="")
                    if len(best_block) > 500:
                        job_data['description'] = best_block
            except Exception as e: print(f"  ⚠️ Next.js Description parse failed: {e}")
            
            # 4. Regex Strategy for Location
            try:
                for pattern in [r'"city"\s*:\s*"(.*?[^\\])"', r'"location"\s*:\s*"(.*?[^\\])"', r'"cityName"\s*:\s*"(.*?)"']:
                    loc_match = re.search(pattern, combined)
                    if loc_match:
                        job_data['location'] = loc_match.group(1).replace('\\"', '"').replace('\\\\', '\\').encode('utf-8').decode('unicode_escape', 'ignore')
                        break
            except Exception as e: print(f"  ⚠️ Next.js Location parse failed: {e}")

            # Final check - be more lenient but verify quality
            if self._is_valid_result(job_data):
                print(f"✅ Extracted data from Next.js hydration (Desc: {len(job_data['description'])} chars)")
                return job_data
            else:
                print(f"  ⚠️ Next.js: Extraction incomplete or invalid. (Title='{job_data['title']}', DescLen={len(job_data['description'])})")
                
        except Exception as e:
            print(f"  ❌ Next.js hydration fatal error: {e}")
        return None
