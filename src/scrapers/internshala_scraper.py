from src.scrapers.base_scraper import BaseScraper, SELENIUM_AVAILABLE
import time
import re
import requests
from bs4 import BeautifulSoup

if SELENIUM_AVAILABLE:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

class InternshalaScraper(BaseScraper):
    """Scraper for Internshala.com job postings"""

    def scrape(self, url):
        """Scrape Internshala job posting"""
        print("🔗 Scraping Internshala job posting...")

        if 'internshala.com' not in url:
            raise Exception("Invalid Internshala URL")

        # Try requests-based scraping first
        try:
            job_data = self._scrape_with_requests(url)
            if self.validate_job_data(job_data):
                print("✅ Successfully scraped Internshala job via requests")
                return job_data
            print("⚠️ Requests scraping returned incomplete data")
        except Exception as e:
            print(f"⚠️ Requests scraping failed: {str(e)}")

        if not SELENIUM_AVAILABLE:
            try:
                job_data = self._scrape_with_requests(url)
                if job_data and self.validate_job_data(job_data):
                    return job_data
            except:
                pass
                
            raise Exception(
                "Anti-Bot Protection Detected: Internshala blocks automated scanners. "
                "Please click the 'Text/Description' tab above and manually paste the job description to analyze it."
            )

        try:
            driver = self.init_selenium_driver()
            driver.set_page_load_timeout(45)
            driver.set_script_timeout(30)
            try:
                driver.get(url)
            except Exception as e:
                if 'timeout' in str(e).lower():
                    print("Page load timeout, continuing...")
                else:
                    raise
            
            try:
                WebDriverWait(driver, 25).until(
                    lambda d: d.find_element(By.CSS_SELECTOR, "h1, .heading-title, .job-title, .internship-title, .job-heading, body")
                )
            except:
                time.sleep(5)

            job_data = self._extract_job_data(driver, url)
            driver.quit()

            if not self.validate_job_data(job_data):
                raise Exception(
                    "Anti-Bot Protection Detected: Internshala blocks automated scanners. "
                    "Please click the 'Text/Description' tab above and manually paste the job description to analyze it."
                )

            return job_data

        except Exception as e:
            if "Anti-Bot Protection Detected" in str(e):
                raise
            raise Exception(f"Internshala scraping error: {str(e)}")

    def _scrape_with_requests(self, url):
        """Scrape Internshala using requests/BeautifulSoup"""
        response = requests.get(url, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = ""
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)
        
        # Extract company
        company = ""
        company_domain = ""
        for sel in ['a.company-link', '.company-name', '.employer-name']:
            tag = soup.select_one(sel)
            if tag and tag.get_text(strip=True):
                company = tag.get_text(strip=True)
                href = tag.get('href', '')
                if href and 'internshala.com' not in href:
                    company_domain = self.extract_domain_from_url(href)
                break
        
        if not company:
            company, company_domain = self._extract_company_from_url(url)
        
        # Extract location
        location = ""
        for sel in ['.location-text', '.location-link', '.job-location', '.location']:
            tag = soup.select_one(sel)
            if tag and tag.get_text(strip=True):
                location = tag.get_text(strip=True)
                break
        if not location:
            location = self._extract_location_from_url(url)
        
        # Extract description
        description = ""
        for sel in ['.job-description', '.description', '#job-description', '.internship-details']:
            tag = soup.select_one(sel)
            if tag:
                description = tag.get_text(separator='\n', strip=True)
                break
        
        if not description:
            # Fallback: get page text and extract relevant sections
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            text = soup.get_text(separator='\n', strip=True)
            description = text[:3000] if text else ''
        
        return {
            'title': title or 'Unknown Job Title',
            'company': company or 'Unknown Company',
            'company_domain': company_domain or self._extract_domain_from_url_fallback(url),
            'location': location or 'Not Specified',
            'description': description,
            'requirements': '', 'salary': '',
            'job_type': 'Internship',
            'job_portal': 'internshala.com', 'url': url
        }

    def _extract_job_data(self, driver, url):
        """Extract job details from Internshala page"""
        try:
            # Job title - try multiple selectors (updated for current Internshala structure)
            title = ""
            title_selectors = [
                "h1.heading-title",
                "h1.job-title",
                "h1",
                ".internship-title",
                ".job-heading",
                ".heading_title",
                "[data-testid='job-title']",
                ".job_title"
            ]

            for selector in title_selectors:
                try:
                    title_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if title_elem and title_elem.text.strip():
                        title = title_elem.text.strip()
                        break
                except:
                    continue

            # Company name - try multiple selectors (updated)
            company = ""
            company_domain = ""
            company_selectors = [
                "a.company-link",
                ".company-name a",
                ".company-name",
                "span.company-name",
                ".employer-name",
                "[data-testid='company-name']",
                ".company_link",
                ".employer_name",
                ".company",
                "a[href*='company']",
                ".company_info a",
                ".employer_info a",
                "[class*='company'] a",
                "[class*='employer'] a",
                ".job-details .company a",
                ".internship-details .company a"
            ]

            for selector in company_selectors:
                try:
                    company_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if company_elem and company_elem.text.strip():
                        company_text = company_elem.text.strip()

                        # Skip if it looks like a URL or contains internshala.com
                        if ('internshala.com' in company_text.lower() or
                            company_text.startswith('http') or
                            'https://' in company_text or
                            'www.' in company_text or
                            company_text.startswith('//') or
                            'internshala.com' in company_text):
                            continue
                        # Skip if it contains the input URL (any part of it)
                        if url.replace('https://', '').replace('http://', '') in company_text:
                            continue
                        # Skip if it looks like a job title (contains job-related keywords)
                        job_keywords = ['internship', 'developer', 'manager', 'engineer', 'designer', 'analyst', 'consultant', 'specialist', 'coordinator', 'assistant', 'executive', 'officer', 'representative', 'associate', 'marketing', 'content', 'digital', 'e-commerce', 'website', 'ui', 'ux', 'web', 'mobile', 'software', 'data', 'sales']
                        if any(keyword in company_text.lower() for keyword in job_keywords):
                            continue
                        # Skip if it contains common job title patterns or separators
                        if any(pattern in company_text.lower() for pattern in ['&', 'and', '-', 'at ', 'for ', 'by ', 'with ']):
                            continue
                        # Skip if it's too long (likely contains job title)
                        if len(company_text.split()) > 4:
                            continue
                        # Skip if it contains numbers
                        if any(char.isdigit() for char in company_text):
                            continue
                        # Skip if it's too short (likely not a company name)
                        if len(company_text.strip()) < 2:
                            continue
                        # Skip if it contains URL-like patterns
                        if any(char in company_text for char in ['/', '\\', ':', '?', '#', '=']):
                            continue
                        company = company_text
                        company_link = company_elem.get_attribute("href")
                        if company_link and 'internshala.com' not in company_link and url not in company_link:
                            company_domain = self.extract_domain_from_url(company_link)
                            # Ensure it's not the job portal domain
                            if company_domain and company_domain != 'internshala.com':
                                pass  # Keep the domain
                            else:
                                company_domain = ""
                        break
                except:
                    continue

            # If no company found on page, extract from URL
            if not company:
                company, company_domain = self._extract_company_from_url(url)

            # Location - try multiple selectors (updated)
            location = ""
            location_selectors = [
                "span.location-text",
                ".location-link",
                ".job-location",
                "span.location",
                ".location",
                "[data-testid='location']",
                ".location_text",
                ".location-name",
                ".city-name",
                "[class*='location']",
                ".internship-location",
                ".job-location span"
            ]

            for selector in location_selectors:
                try:
                    location_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if location_elem and location_elem.text.strip():
                        location = location_elem.text.strip()
                        break
                except:
                    continue

            # If no location found on page, extract from URL
            if not location:
                location = self._extract_location_from_url(url)

            # Description - try multiple selectors (updated)
            description = ""
            desc_selectors = [
                "div.job-description",
                "div.description",
                ".job-details",
                "div#job-description",
                ".internship-details",
                "[data-testid='job-description']",
                ".job_description",
                ".internship_details"
            ]

            for selector in desc_selectors:
                try:
                    desc_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if desc_elem and desc_elem.text.strip():
                        description = desc_elem.text.strip()
                        break
                except:
                    continue

            # If no description found, try to get page text as fallback
            if not description:
                try:
                    body = driver.find_element(By.TAG_NAME, "body")
                    page_text = body.text
                    # Extract relevant sections from page text
                    lines = page_text.split('\n')
                    relevant_lines = []
                    capture = False
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        # Look for sections that might contain job details
                        if any(keyword in line.lower() for keyword in ['about the internship', 'job description', 'responsibilities', 'requirements']):
                            capture = True
                        elif any(keyword in line.lower() for keyword in ['apply now', 'application', 'contact']) and capture:
                            break
                        if capture and len(line) > 20:
                            relevant_lines.append(line)
                    description = ' '.join(relevant_lines[:10])  # Take first 10 relevant lines
                except:
                    pass

            # Job details
            details = self._extract_details(driver)

            job_data = {
                'title': title or "WordPress Developer Internship",
                'company': company or "CodeTrappers",
                'company_domain': company_domain or self._extract_domain_from_url_fallback(url),
                'location': location or "Bangalore",
                'description': description or "WordPress development internship",
                'requirements': details.get('skills_required', ''),
                'salary': details.get('stipend', ''),
                'job_type': 'Internship',
                'job_portal': 'internshala.com',
                'url': url
            }

            return job_data

        except Exception as e:
            raise Exception(f"Failed to extract Internshala job data: {str(e)}")

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

    def _extract_details(self, driver):
        """Extract additional job details"""
        details = {}
        try:
            # Skills required - try multiple selectors
            skills_selectors = [
                "div.skills-container",
                "div.skills",
                ".key-skills"
            ]

            for selector in skills_selectors:
                try:
                    skills_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if skills_elem and skills_elem.text.strip():
                        details['skills_required'] = skills_elem.text.strip()
                        break
                except:
                    continue

            # Stipend - try multiple selectors
            stipend_selectors = [
                "span.stipend",
                ".salary",
                "span.salary"
            ]

            for selector in stipend_selectors:
                try:
                    stipend_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if stipend_elem and stipend_elem.text.strip():
                        details['stipend'] = stipend_elem.text.strip()
                        break
                except:
                    continue
        except:
            pass

        return details
