from src.scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

class NaukriScraper(BaseScraper):
    """Scraper for Naukri.com job postings"""

    def scrape(self, url):
        """Scrape Naukri job posting"""
        print("🔗 Scraping Naukri job posting...")

        if 'naukri.com' not in url:
            raise Exception("Invalid Naukri URL")

        driver = None
        try:
            driver = self.init_selenium_driver()

            # Add headers to mimic real browser
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })

            driver.get(url)

            # Wait for page to load - try multiple possible selectors with longer timeout
            try:
                WebDriverWait(driver, 20).until(
                    lambda d: d.find_element(By.CSS_SELECTOR, "h1, .job-title, .jd-header-title, .jobTitle, body")
                )
            except:
                # If page doesn't load properly, still try to extract what we can
                time.sleep(5)  # Give extra time for dynamic content
                print("⚠️ Page load timeout, attempting extraction anyway...")

            job_data = self._extract_job_data(driver, url)

            if not self.validate_job_data(job_data):
                print("⚠️ Validation failed, but returning partial data")
                # Don't raise exception, return what we have

            return job_data

        except Exception as e:
            error_msg = f"Naukri scraping error: {str(e)}"
            print(f"❌ {error_msg}")

            # Return minimal data instead of failing completely
            return {
                'title': 'Unable to extract title',
                'company': 'Unable to extract company',
                'company_domain': '',
                'location': 'Unable to extract location',
                'description': f'Error: {error_msg}',
                'requirements': '',
                'job_type': '',
                'experience_level': '',
                'salary': '',
                'company_profile': '',
                'job_portal': 'naukri.com',
                'url': url,
                'error': error_msg
            }
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def _extract_job_data(self, driver, url):
        """Extract job details from Naukri page"""
        try:
            # Job title - try multiple selectors
            title = ""
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
            company = ""
            company_domain = ""
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
            location = ""
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
            description = ""
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
