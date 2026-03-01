import re
from src.scrapers.base_scraper import BaseScraper, SELENIUM_AVAILABLE

if SELENIUM_AVAILABLE:
    from selenium.webdriver.common.by import By


class IndeedScraper(BaseScraper):
    """Scraper for Indeed.com job postings"""
    
    def scrape(self, url):
        """Scrape Indeed job posting"""
        print("🔗 Scraping Indeed job posting...")
        
        if 'indeed.com' not in url:
            raise Exception("Invalid Indeed URL")
        
        try:
            return self.scrape_with_fallback(url, "Indeed")
        except Exception as e:
            raise Exception(f"Indeed scraping error: {str(e)}")
    
    def scrape_with_requests(self, url):
        """Scrape Indeed using requests/BeautifulSoup"""
        page_text, soup = self.get_page_text(url)
        
        # Extract title
        title = ""
        title_tag = soup.find('h1')
        if title_tag:
            title = title_tag.get_text(strip=True)
        
        # Extract company
        company = ""
        company_selectors = [
            {'attrs': {'data-company-name': 'true'}},
            {'attrs': {'data-testid': 'company-name'}},
            {'attrs': {'data-testid': 'inlineHeader-companyName'}},
        ]
        for sel in company_selectors:
            tag = soup.find('div', **sel) or soup.find('span', **sel)
            if tag:
                company = tag.get_text(strip=True)
                break
        
        # Extract location
        location = ""
        loc_selectors = [
            {'attrs': {'data-testid': 'job-location'}},
            {'attrs': {'data-testid': 'inlineHeader-companyLocation'}},
        ]
        for sel in loc_selectors:
            tag = soup.find('div', **sel) or soup.find('span', **sel)
            if tag:
                location = tag.get_text(strip=True)
                break
        
        # Extract description
        description = ""
        desc_selectors = [
            {'id': 'jobDescriptionText'},
            {'attrs': {'data-testid': 'job-description'}},
            {'class_': 'jobsearch-jobDescriptionText'},
        ]
        for sel in desc_selectors:
            tag = soup.find('div', **sel)
            if tag:
                description = tag.get_text(separator='\n', strip=True)
                break
        
        # If no structured extraction worked, use the full page text
        if not description and page_text:
            description = page_text[:3000]
        
        # Extract salary from metadata
        salary = ""
        salary_tag = soup.find('div', id='salaryInfoAndJobType')
        if salary_tag:
            salary = salary_tag.get_text(strip=True)
        
        job_data = {
            'title': title or 'Unknown Job Title',
            'company': company or 'Unknown Company',
            'company_domain': '',
            'location': location or 'Not Specified',
            'description': description,
            'requirements': '',
            'salary': salary,
            'company_profile': '',
            'job_type': '',
            'job_portal': 'indeed.com',
            'url': url
        }
        
        return job_data
    
    def scrape_with_selenium(self, url):
        """Scrape Indeed using Selenium (original method)"""
        driver = self.init_selenium_driver()
        try:
            driver.get(url)
            job_data = self._extract_job_data_selenium(driver)
            return job_data
        finally:
            driver.quit()
    
    def _extract_job_data_selenium(self, driver):
        """Extract job details from Indeed page using Selenium"""
        # Job title
        title = ""
        title_selectors = [
            "h1.jobsearch-JobInfoHeader-title",
            "h1[data-testid='jobsearch-JobInfoHeader-title']",
            "h1"
        ]
        for selector in title_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                if elem and elem.text.strip():
                    title = elem.text.strip()
                    break
            except:
                continue

        # Company name
        company = ""
        company_selectors = [
            "div[data-company-name='true']",
            "span[data-testid='company-name']",
            "div[data-testid='inlineHeader-companyName']",
        ]
        for selector in company_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                if elem and elem.text.strip():
                    company = elem.text.strip()
                    break
            except:
                continue

        # Location
        location = ""
        location_selectors = [
            "div[data-testid='job-location']",
            "span[data-testid='job-location']",
            "div[data-testid='inlineHeader-companyLocation']",
        ]
        for selector in location_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                if elem and elem.text.strip():
                    location = elem.text.strip()
                    break
            except:
                continue

        # Description
        description = ""
        desc_selectors = [
            "div#jobDescriptionText",
            "div[data-testid='job-description']",
            "div.jobsearch-jobDescriptionText",
        ]
        for selector in desc_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                if elem and elem.text.strip():
                    description = elem.text.strip()
                    break
            except:
                continue

        return {
            'title': title or 'Unknown Job Title',
            'company': company or 'Unknown Company',
            'company_domain': '',
            'location': location or 'Not Specified',
            'description': description,
            'requirements': '',
            'salary': '',
            'company_profile': '',
            'job_type': '',
            'job_portal': 'indeed.com',
            'url': driver.current_url
        }