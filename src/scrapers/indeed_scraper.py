import json
import re
import cloudscraper
import urllib.parse
import requests
from bs4 import BeautifulSoup
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
            # Extract Indeed Job ID (jk parameter)
            job_id = None
            if 'vjk=' in url:
                job_id = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get('vjk', [None])[0]
            elif 'jk=' in url:
                job_id = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get('jk', [None])[0]

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

            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )

            # Attempt Mobile API Bypass first (less strict cloudflare)
            if job_id:
                try:
                    mobile_api_url = f"https://www.indeed.com/m/basecamp/viewjob?viewtype=embedded&jk={job_id}"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
                        'Accept': 'application/json',
                    }
                    api_resp = scraper.get(mobile_api_url, headers=headers, timeout=10)
                    if api_resp.status_code == 200:
                        data = api_resp.json()
                        if 'jobTitle' in data: job_data['title'] = data['jobTitle']
                        if 'companyInfo' in data and 'companyName' in data['companyInfo']: 
                            job_data['company'] = data['companyInfo']['companyName']
                        if 'jobDescriptionText' in data:
                            job_data['description'] = BeautifulSoup(data['jobDescriptionText'], "html.parser").get_text(separator="\n").strip()
                        
                        if job_data['title'] != 'Unknown Job Title' and job_data['company'] != 'Unknown Company':
                            return job_data # Success via mobile API!
                except Exception:
                    pass # Fallback to standard cloudscraper HTML

            # 1. Fetch raw HTML using Cloudscraper to bypass Cloudflare blocks
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
            
            response = scraper.get(url, headers=headers, timeout=15)
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
            if e.response.status_code == 403 or e.response.status_code == 429:
                error_msg = "Indeed is blocking automated scraping (403/429). Please copy and paste the Job Title, Company, and Description manually into the application."
            else:
                error_msg = f"Indeed requests scraping error: {str(e)}"
                
            print(f"❌ {error_msg}")
            
            return {
                'title': 'Manual Entry Required',
                'company': 'Manual Entry Required',
                'company_domain': '',
                'location': 'Manual Entry Required',
                'description': error_msg,
                'job_type': '',
                'salary': '',
                'job_portal': 'indeed.com',
                'url': url,
                'error': error_msg
            }
        except Exception as e:
            # Check for Cloudscraper 403 string error (cloudflare blocking)
            if "403" in str(e) or "captcha" in str(e).lower():
                error_msg = "Indeed is blocking automated scraping (Captcha/403). Please copy and paste the Job Title, Company, and Description manually into the application."
            else:
                error_msg = f"Indeed requests scraping error: {str(e)}"
                
            print(f"❌ {error_msg}")
            
            return {
                'title': 'Manual Entry Required',
                'company': 'Manual Entry Required',
                'company_domain': '',
                'location': 'Manual Entry Required',
                'description': error_msg,
                'job_type': '',
                'salary': '',
                'job_portal': 'indeed.com',
                'url': url,
                'error': error_msg
            }