from src.scrapers.base_scraper import BaseScraper
import json
import re
import requests
from bs4 import BeautifulSoup

class IndeedScraper(BaseScraper):
    """Scraper for Indeed.com job postings"""
    
    def scrape(self, url):
        """Scrape Indeed job posting bypassing Selenium"""
        print("🔗 Scraping Indeed job posting via Requests API...")
        
        if 'indeed.com' not in url:
            raise Exception("Invalid Indeed URL")
        
        try:
            # 1. Fetch raw HTML using Requests
            # Indeed is notorious for blocking standard requests, so we need strong headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_data = {
                'title': 'Unknown Job Title',
                'company': 'Unknown Company',
                'company_domain': '',
                'location': 'Not Specified',
                'description': 'No description available',
                'job_type': '',
                'salary': '',
                'job_portal': 'indeed.com',
                'url': url
            }
            
            # 2. Extract Data directly from structured JSON-LD (Indeed usually includes this)
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                        if 'title' in data:
                            job_data['title'] = data['title']
                        if 'description' in data:
                            raw_desc = data['description']
                            clean_desc = BeautifulSoup(raw_desc, "html.parser").get_text(separator="\n").strip()
                            job_data['description'] = clean_desc
                        
                        if 'hiringOrganization' in data:
                            org = data['hiringOrganization']
                            if isinstance(org, dict) and 'name' in org:
                                job_data['company'] = org['name']
                            if isinstance(org, dict) and 'sameAs' in org:
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
                except Exception as e:
                    continue
                    
            # 3. HTML Fallbacks if JSON-LD is missing
            if job_data['title'] == 'Unknown Job Title':
                title_elem = soup.select_one("h1.jobsearch-JobInfoHeader-title") or soup.find("h1")
                if title_elem: job_data['title'] = title_elem.get_text().strip()

            if job_data['company'] == 'Unknown Company':
                comp_elem = soup.select_one("div[data-company-name='true']") or soup.select_one("span[data-testid='company-name']")
                if comp_elem: job_data['company'] = comp_elem.get_text().strip()
                
            if job_data['location'] == 'Not Specified':
                loc_elem = soup.select_one("div[data-testid='inlineHeader-companyLocation']") or soup.select_one("div[data-testid='job-location']")
                if loc_elem: job_data['location'] = loc_elem.get_text().strip()
                
            if job_data['description'] == 'No description available':
                desc_elem = soup.select_one("div#jobDescriptionText") or soup.select_one("div.jobsearch-jobDescriptionText")
                if desc_elem: job_data['description'] = desc_elem.get_text(separator="\n").strip()

            if not self.validate_job_data(job_data):
                print("⚠️ Validation failed, but returning partial requests data")
            
            return job_data
            
        except requests.exceptions.HTTPError as e:
            # Indeed is notorious for throwing 403 Forbidden to block bots. Handle gracefully.
            if e.response.status_code == 403:
                error_msg = f"Indeed actively blocked the request (403 Forbidden). Try using a proxy or entering data manually."
            else:
                error_msg = f"Indeed requests scraping error: {str(e)}"
                
            print(f"❌ {error_msg}")
            
            return {
                'title': 'Unable to extract title',
                'company': 'Unable to extract company',
                'company_domain': '',
                'location': 'Unable to extract location',
                'description': f'Error: {error_msg}',
                'job_type': '',
                'salary': '',
                'job_portal': 'indeed.com',
                'url': url,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Indeed requests scraping error: {str(e)}"
            print(f"❌ {error_msg}")
            
            return {
                'title': 'Unable to extract title',
                'company': 'Unable to extract company',
                'company_domain': '',
                'location': 'Unable to extract location',
                'description': f'Error: {error_msg}',
                'job_type': '',
                'salary': '',
                'job_portal': 'indeed.com',
                'url': url,
                'error': error_msg
            }