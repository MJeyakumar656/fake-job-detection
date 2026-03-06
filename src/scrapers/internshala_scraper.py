from src.scrapers.base_scraper import BaseScraper
import json
import re
import requests
from bs4 import BeautifulSoup

class InternshalaScraper(BaseScraper):
    """Scraper for Internshala.com job postings"""

    def scrape(self, url):
        """Scrape Internshala job posting bypassing Selenium"""
        print("🔗 Scraping Internshala job posting via Requests API...")

        if 'internshala.com' not in url:
            raise Exception("Invalid Internshala URL")

        try:
            # 1. Fetch raw HTML using Requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
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
                'requirements': '',
                'job_type': 'Internship',
                'experience_level': '',
                'salary': '',
                'company_profile': '',
                'job_portal': 'internshala.com',
                'url': url
            }

            # 2. Extract Data directly from structured JSON-LD
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
                title_elem = soup.select_one("h1.job-title") or soup.find("h1")
                if title_elem: job_data['title'] = title_elem.get_text().strip()

            if job_data['company'] == 'Unknown Company':
                comp_elem = soup.select_one("div.company-name") or soup.select_one("a.company-link")
                if comp_elem: job_data['company'] = comp_elem.get_text().strip()
                
            if job_data['description'] == 'No description available':
                desc_elem = soup.select_one("div.job-description") or soup.select_one("div.internship_details")
                if desc_elem: job_data['description'] = desc_elem.get_text(separator="\n").strip()

            if not job_data['company_domain']:
                job_data['company'], job_data['company_domain'] = self._extract_company_from_url(url)

            if not self.validate_job_data(job_data):
                print("⚠️ Validation failed, but returning partial requests data")

            return job_data

        except Exception as e:
            error_msg = f"Internshala requests scraping error: {str(e)}"
            print(f"❌ {error_msg}")

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
                'job_portal': 'internshala.com',
                'url': url,
                'error': error_msg
            }

    def _extract_company_from_url(self, url):
        """Extract company name and domain from Internshala URL"""
        try:
            if 'internshala.com' in url:
                # URL structure: ...internship-detail/[job-details]-at-[company-name][numbers]
                # Split by "-at-" and take the last part
                parts = url.split('-at-')
                if len(parts) > 1:
                    company_part = parts[-1]  # Take the last part after "-at-"
                    # Remove query parameters first
                    company_part = company_part.split('?')[0]
                    # Remove numbers from the end
                    company_slug = re.sub(r'\d+$', '', company_part)
                    # Remove any trailing hyphens
                    company_slug = company_slug.rstrip('-')

                    if company_slug:
                        # Convert slug to proper company name
                        company_name = company_slug.replace('-', ' ').title()

                        # Try to construct domain from company name
                        # Remove common words and create domain
                        domain_base = re.sub(r'\b(the|and|or|of|in|on|at|to|for|with)\b', '', company_slug, flags=re.IGNORECASE)
                        domain_base = re.sub(r'-+', '-', domain_base.strip('-'))
                        domain_base = domain_base.replace('-', '')

                        if domain_base:
                            possible_domains = [
                                f"{domain_base}.com",
                                f"{domain_base}.in",
                                f"{domain_base}.co.in",
                                f"www.{domain_base}.com",
                                f"www.{domain_base}.in"
                            ]

                            # Try to verify if domain exists (basic check)
                            for domain in possible_domains:
                                if self._verify_domain_exists(domain):
                                    return company_name, domain

                            # If no domain verified, don't return unverified domain
                            return company_name, ""

                        return company_name, ""  # Return company name if domain construction fails
            return "", ""
        except:
            return "", ""

    def _extract_location_from_url(self, url):
        """Extract location from Internshala URL"""
        try:
            if 'internshala.com' in url:
                # URL structure: ...internship-detail/[job-title]-in-[location]-at-[company]...
                # Look for "-in-" followed by location, stopping before "-at-"
                import re
                match = re.search(r'-in-([a-zA-Z]+(?:-[a-zA-Z]+)*?)(?=-at-)', url)
                if match:
                    location_slug = match.group(1)
                    # Convert slug to proper location name
                    location = location_slug.replace('-', ' ').title()
                    return location
            return ""
        except:
            return ""

    def _extract_domain_from_url_fallback(self, url):
        """Extract domain from URL as fallback"""
        company_name, domain = self._extract_company_from_url(url)
        return domain

    def _verify_domain_exists(self, domain):
        """Basic domain verification"""
        try:
            import socket
            # Remove www. prefix for DNS check
            check_domain = domain.replace('www.', '')
            socket.gethostbyname(check_domain)
            return True
        except:
            return False


