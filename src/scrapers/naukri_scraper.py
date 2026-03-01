from src.scrapers.base_scraper import BaseScraper, SELENIUM_AVAILABLE
import time
import re
import requests
from bs4 import BeautifulSoup
import json

if SELENIUM_AVAILABLE:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

class NaukriScraper(BaseScraper):
    """Scraper for Naukri.com job postings"""

    def scrape(self, url):
        """Scrape Naukri job posting"""
        print("🔗 Scraping Naukri job posting...")

        if 'naukri.com' not in url:
            raise Exception("Invalid Naukri URL")

        # Try requests-based scraping first (works everywhere including Render)
        try:
            job_data = self._scrape_with_requests(url)
            if self.validate_job_data(job_data):
                print("✅ Successfully scraped Naukri job via requests")
                return job_data
            print("⚠️ Requests scraping returned incomplete data")
        except Exception as e:
            print(f"⚠️ Requests scraping failed: {str(e)}")

        # Try Selenium if available
        if not SELENIUM_AVAILABLE:
            try:
                job_data = self._scrape_with_requests(url)
                if job_data and self.validate_job_data(job_data):
                    return job_data
            except:
                pass
                
            raise Exception(
                "Anti-Bot Protection Detected: Naukri blocks automated scanners. "
                "Please click the 'Text/Description' tab above and manually paste the job description to analyze it."
            )

        driver = None
        try:
            driver = self.init_selenium_driver()

            # Add headers to mimic real browser
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })

            driver.get(url)
            
            # Wait for page to fully load
            time.sleep(3)
            
            # Scroll down to trigger lazy loading
            try:
                driver.execute_script("window.scrollTo(0, 500);")
            except Exception:
                pass
            time.sleep(2)
            
            # Wait for page to load
            try:
                WebDriverWait(driver, 30).until(
                    lambda d: d.find_element(By.CSS_SELECTOR, "h1, .job-title, .jd-header-title, .jobTitle, body")
                )
            except:
                time.sleep(5)
                print("⚠️ Page load timeout, attempting extraction anyway...")

            time.sleep(3)
            
            job_data = self._extract_job_data(driver, url)

            if not self.validate_job_data(job_data):
                raise Exception(
                    "Anti-Bot Protection Detected: Naukri blocks automated scanners. "
                    "Please click the 'Text/Description' tab above and manually paste the job description to analyze it."
                )

            return job_data

        except Exception as e:
            error_msg = f"Naukri scraping error: {str(e)}"
            print(f"❌ {error_msg}")

            return {
                'title': 'Unable to extract title',
                'company': 'Unable to extract company',
                'company_domain': '',
                'location': 'Unable to extract location',
                'description': f'Error: {error_msg}',
                'requirements': '', 'job_type': '', 'experience_level': '',
                'salary': '', 'company_profile': '',
                'job_portal': 'naukri.com', 'url': url,
                'error': error_msg
            }
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def _scrape_with_requests(self, url):
        """Scrape Naukri using requests/BeautifulSoup + JSON-LD (with optional ScraperAPI)"""
        import os
        api_key = os.environ.get('SCRAPER_API_KEY')
        if api_key:
            from urllib.parse import urlencode
            payload = {'api_key': api_key, 'url': url, 'render_js': 'true'}
            proxy_url = 'https://api.scraperapi.com/?' + urlencode(payload)
            response = requests.get(proxy_url, timeout=45)
        else:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        data = {}
        
        # Try JSON-LD structured data first (most reliable)
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                json_content = script.string
                if json_content and 'JobPosting' in json_content:
                    job_json = json.loads(json_content)
                    data['title'] = job_json.get('title', '')
                    org = job_json.get('hiringOrganization', {})
                    if isinstance(org, dict):
                        data['company'] = org.get('name', '')
                        data['company_domain'] = org.get('sameAs', '')
                    loc = job_json.get('jobLocation', {})
                    if isinstance(loc, dict) and 'address' in loc:
                        addr = loc.get('address', {})
                        if isinstance(addr, dict):
                            parts = [addr.get('addressLocality', ''), addr.get('addressRegion', '')]
                            data['location'] = ', '.join(p for p in parts if p)
                    data['description'] = job_json.get('description', '')
                    data['job_type'] = job_json.get('employmentType', '')
                    break
            except:
                continue
        
        # Supplement with HTML selectors
        if not data.get('title'):
            h1 = soup.find('h1')
            if h1:
                data['title'] = h1.get_text(strip=True)
        
        if not data.get('description'):
            for sel in [{'class_': re.compile(r'desc')}, {'class_': re.compile(r'job-description')}]:
                tag = soup.find('div', **sel)
                if tag:
                    data['description'] = tag.get_text(separator='\n', strip=True)
                    break
        
        return {
            'title': data.get('title', 'Unknown Job Title'),
            'company': data.get('company', 'Unknown Company'),
            'company_domain': data.get('company_domain', ''),
            'location': data.get('location', 'Not Specified'),
            'description': data.get('description', ''),
            'requirements': '', 'job_type': data.get('job_type', ''),
            'experience_level': '', 'salary': '',
            'company_profile': '',
            'job_portal': 'naukri.com', 'url': url
        }

    def _extract_from_json_ld(self, driver):
        """Extract job data from JSON-LD structured data"""
        data = {}
        try:
            # Find all script tags with type application/ld+json
            scripts = driver.find_elements(By.CSS_SELECTOR, "script[type='application/ld+json']")
            
            for script in scripts:
                try:
                    json_content = script.get_attribute('innerHTML')
                    if json_content and 'JobPosting' in json_content:
                        import json
                        job_data = json.loads(json_content)
                        
                        # Extract title
                        if 'title' in job_data:
                            data['title'] = job_data.get('title', '')
                        
                        # Extract company name
                        if 'hiringOrganization' in job_data:
                            org = job_data.get('hiringOrganization', {})
                            if isinstance(org, dict):
                                data['company'] = org.get('name', '')
                                if 'sameAs' in org:
                                    data['company_domain'] = org.get('sameAs', '')
                                
                        # Extract location
                        if 'jobLocation' in job_data:
                            loc = job_data.get('jobLocation', {})
                            if isinstance(loc, dict) and 'address' in loc:
                                address = loc.get('address', {})
                                if isinstance(address, dict):
                                    locality = address.get('addressLocality', '')
                                    region = address.get('addressRegion', '')
                                    if locality or region:
                                        location_parts = [p for p in [locality, region] if p]
                                        data['location'] = ', '.join(location_parts)
                                
                        # Extract description
                        if 'description' in job_data:
                            data['description'] = job_data.get('description', '')
                            
                        # Extract experience
                        if 'experienceRequirements' in job_data:
                            exp = job_data.get('experienceRequirements', {})
                            if isinstance(exp, dict):
                                data['experience'] = exp.get('monthsOfExperience', '')
                                
                        # Extract employment type
                        if 'employmentType' in job_data:
                            data['job_type'] = job_data.get('employmentType', '')
                            
                        # Extract salary
                        if 'baseSalary' in job_data:
                            salary = job_data.get('baseSalary', {})
                            if isinstance(salary, dict):
                                value = salary.get('value', {})
                                if isinstance(value, dict):
                                    data['salary'] = f"{value.get('value', '')} {value.get('unitText', '')}"
                        
                        break
                except Exception as e:
                    print(f"⚠️ Error parsing JSON-LD: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"⚠️ Error extracting JSON-LD: {str(e)}")
            
        return data
    
    def _extract_job_data(self, driver, url):
        """Extract job details from Naukri page"""
        try:
            # First, try to extract from JSON-LD structured data
            json_ld_data = self._extract_from_json_ld(driver)
            
            # Job title - try multiple selectors
            title = json_ld_data.get('title', '')
            if not title:
                title_selectors = [
                    "h1.styles_jd-header-title__rZwM1",  # Found working selector
                    "h1",
                    "h1.jd-header-title",
                    "h1.job-title",
                    ".job-title",
                    "[data-testid='job-title']",
                    ".jd-header-title",
                    ".jobTitle",
                    ".job_title",
                    "[class*='title']"
                ]

                for selector in title_selectors:
                    try:
                        title_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        if title_elem and title_elem.text.strip():
                            title = title_elem.text.strip()
                            break
                    except:
                        continue

            # Company name and link - try multiple selectors
            company = json_ld_data.get('company', '')
            company_domain = json_ld_data.get('company_domain', '')
            if not company:
                company_selectors = [
                    "div.styles_jd-header-comp-name__MvqAI a",  # Found working selector
                    "[class*='company']",
                    "a.comp-name",
                    "a.company-name",
                    "div.company-name a",
                    ".company-name a",
                    ".comp-name",
                    "[data-testid='company-name'] a",
                    ".companyName a",
                    ".employer a",
                    "a[href*='company']"
                ]

                for selector in company_selectors:
                    try:
                        company_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        if company_elem and company_elem.text.strip():
                            company_text = company_elem.text.strip()
                            # Skip if it looks like a URL
                            if 'naukri.com' in company_text.lower() or company_text.startswith('http'):
                                continue
                            company = company_text
                            company_link = company_elem.get_attribute("href")
                            if company_link and 'naukri.com' not in company_link:
                                company_domain = self.extract_domain_from_url(company_link)
                            break
                    except:
                        continue

            # Location - try multiple selectors
            location = json_ld_data.get('location', '')
            if not location:
                location_selectors = [
                    "[class*='location']",  # Found working selector
                    "[class*='loc']",  # Found working selector
                    "span.locStd",
                    "span.location",
                    "div.location",
                    ".location",
                    "[data-testid='location']",
                    ".job-location",
                    ".location-text",
                    ".styles_jhc__loc___Du2H",  # Specific selector from page inspection
                    ".styles_jhc__location__W_pVs"  # Specific selector from page inspection
                ]

                for selector in location_selectors:
                    try:
                        location_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        if location_elem and location_elem.text.strip():
                            location = location_elem.text.strip()
                            break
                    except:
                        continue

            # Fallback: Extract location from URL if not found on page
            if not location:
                # Extract cities from URL path
                url_parts = url.split('/')
                if len(url_parts) > 1:
                    job_slug = url_parts[-1].split('?')[0]  # Remove query params
                    # Look for city names in the slug
                    cities = []
                    city_keywords = ['kolkata', 'mumbai', 'delhi', 'hyderabad', 'pune', 'chennai', 'bengaluru', 'bangalore', 'ahmedabad', 'jaipur', 'surat', 'remote']
                    for city in city_keywords:
                        if city in job_slug.lower():
                            if city == 'delhi':
                                cities.append('New Delhi')
                            elif city == 'bengaluru' or city == 'bangalore':
                                cities.append('Bengaluru')
                            else:
                                cities.append(city.title())

                    if cities:
                        location = ', '.join(cities)
                    elif 'remote' in job_slug.lower():
                        location = 'Remote'

            # Description - try multiple selectors
            description = json_ld_data.get('description', '')
            if not description:
                desc_selectors = [
                    "div.styles_JDC__dang-inner-html__h0K4t",  # Found working selector
                    "[class*='desc']",
                    "div.dummyDiv",
                    "div.job-description",
                    "div.description",
                    ".job-description",
                    "[data-testid='job-description']",
                    ".jd-desc",
                    ".jobDesc",
                    ".job_description"
                ]

                for selector in desc_selectors:
                    try:
                        desc_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        if desc_elem and desc_elem.text.strip():
                            description = desc_elem.text.strip()
                            break
                    except:
                        continue

            # Job details
            job_details = self._extract_job_details(driver)
            
            job_data = {
                'title': title,
                'company': company,
                'company_domain': company_domain,
                'location': location,
                'description': description,
                'requirements': job_details.get('key_skills', ''),
                'job_type': job_details.get('job_type', ''),
                'experience_level': job_details.get('experience', ''),
                'salary': job_details.get('salary', ''),
                'company_profile': job_details.get('company_profile', ''),
                'job_portal': 'naukri.com',
                'url': url
            }
            
            return job_data
            
        except Exception as e:
            raise Exception(f"Failed to extract Naukri job data: {str(e)}")
    
    def _extract_job_details(self, driver):
        """Extract additional job details"""
        details = {}
        try:
            # Key skills - try multiple selectors
            skills_selectors = [
                "div.keySkills",
                "div.skills",
                "div.key-skills"
            ]

            for selector in skills_selectors:
                try:
                    skills_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if skills_elem and skills_elem.text.strip():
                        details['key_skills'] = skills_elem.text.strip()
                        break
                except:
                    continue

            # Job type - try multiple selectors
            job_type_selectors = [
                "span.jobType",
                "span.job-type",
                "div.job-type"
            ]

            for selector in job_type_selectors:
                try:
                    job_type_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if job_type_elem and job_type_elem.text.strip():
                        details['job_type'] = job_type_elem.text.strip()
                        break
                except:
                    continue

            # Experience - try multiple selectors
            exp_selectors = [
                "span.expVal",
                "span.experience",
                "div.experience"
            ]

            for selector in exp_selectors:
                try:
                    exp_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if exp_elem and exp_elem.text.strip():
                        details['experience'] = exp_elem.text.strip()
                        break
                except:
                    continue

            # Salary - try multiple selectors
            salary_selectors = [
                "span.salary",
                "div.salary",
                "span.salary-range"
            ]

            for selector in salary_selectors:
                try:
                    salary_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if salary_elem and salary_elem.text.strip():
                        details['salary'] = salary_elem.text.strip()
                        break
                except:
                    continue

            # Company profile - try multiple selectors
            profile_selectors = [
                "div.company-profile",
                "div.company-info",
                "div.about-company"
            ]

            for selector in profile_selectors:
                try:
                    profile_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if profile_elem and profile_elem.text.strip():
                        details['company_profile'] = profile_elem.text.strip()
                        break
                except:
                    continue
        except:
            pass

        return details
