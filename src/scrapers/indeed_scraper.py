from src.scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class IndeedScraper(BaseScraper):
    """Scraper for Indeed.com job postings"""
    
    def scrape(self, url):
        """Scrape Indeed job posting"""
        print("🔗 Scraping Indeed job posting...")
        
        if 'indeed.com' not in url:
            raise Exception("Invalid Indeed URL")
        
        try:
            driver = self.init_selenium_driver()
            driver.get(url)
            
            job_data = self._extract_job_data(driver)
            driver.quit()
            
            if not self.validate_job_data(job_data):
                raise Exception("Failed to extract complete job data")
            
            return job_data
            
        except Exception as e:
            raise Exception(f"Indeed scraping error: {str(e)}")
    
    def _extract_job_data(self, driver):
        """Extract job details from Indeed page"""
        try:
            # Job title - try multiple selectors for better compatibility
            title = ""
            title_selectors = [
                "h1.jobsearch-JobInfoHeader-title",
                "h1[data-testid='jobsearch-JobInfoHeader-title']",
                "h1.icl-u-xs-mb--xs.icl-u-xs-mt--none.jobsearch-JobInfoHeader-title",
                "h1"
            ]

            for selector in title_selectors:
                try:
                    title_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if title_elem and title_elem.text.strip():
                        title = title_elem.text.strip()
                        break
                except:
                    continue

            # Company name - try multiple selectors
            company = ""
            company_selectors = [
                "div.jobsearch-InlineCompanyRating span",
                "div[data-company-name='true']",
                "span[data-testid='company-name']",
                "div[data-testid='inlineHeader-companyName']",
                "a[data-tn-element='companyName']"
            ]

            for selector in company_selectors:
                try:
                    company_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if company_elem and company_elem.text.strip():
                        company = company_elem.text.strip()
                        break
                except:
                    continue

            # Company domain
            company_domain = ""
            try:
                company_link_selectors = [
                    "a.companyHeader-link",
                    "a[data-tn-element='companyName']",
                    "a[data-testid='company-name-link']"
                ]
                for selector in company_link_selectors:
                    try:
                        company_link_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        if company_link_elem:
                            company_link = company_link_elem.get_attribute("href")
                            if company_link:
                                company_domain = self.extract_domain_from_url(company_link)
                                break
                    except:
                        continue
            except:
                pass

            # Location - try multiple selectors
            location = ""
            location_selectors = [
                "div.jobsearch-JobMetadataHeader-iconLabel",
                "div[data-testid='job-location']",
                "span[data-testid='job-location']",
                "div[data-testid='inlineHeader-companyLocation']",
                "div.jobsearch-JobMetadataHeader-item"
            ]

            for selector in location_selectors:
                try:
                    location_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if location_elem and location_elem.text.strip():
                        location = location_elem.text.strip()
                        break
                except:
                    continue

            # Description - try multiple selectors
            description = ""
            desc_selectors = [
                "div#jobDescriptionText",
                "div[data-testid='job-description']",
                "div.jobsearch-jobDescriptionText",
                "div[data-tn-component='jobDescription']"
            ]

            for selector in desc_selectors:
                try:
                    desc_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if desc_elem and desc_elem.text.strip():
                        description = desc_elem.text.strip()
                        break
                except:
                    continue
            
            # Job type and salary
            job_details = self._get_job_details(driver)
            
            job_data = {
                'title': title,
                'company': company,
                'company_domain': company_domain,
                'location': location,
                'description': description,
                'job_type': job_details.get('job_type', ''),
                'salary': job_details.get('salary', ''),
                'job_portal': 'indeed.com',
                'url': driver.current_url
            }
            
            return job_data
            
        except Exception as e:
            raise Exception(f"Failed to extract Indeed job data: {str(e)}")
    
    def _get_job_details(self, driver):
        """Extract job type and salary"""
        details = {}
        try:
            metadata = driver.find_elements(By.CSS_SELECTOR, "div.jobsearch-JobMetadataHeader-item")
            
            for item in metadata:
                text = item.text
                if 'Full-time' in text or 'Part-time' in text:
                    details['job_type'] = text
                elif '$' in text or 'salary' in text.lower():
                    details['salary'] = text
        except:
            pass
        
        return details