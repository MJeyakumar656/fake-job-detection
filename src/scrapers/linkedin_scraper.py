from src.scrapers.base_scraper import BaseScraper, SELENIUM_AVAILABLE
import time
import re
import requests
from bs4 import BeautifulSoup
import os

if SELENIUM_AVAILABLE:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options

class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn job postings with authentication support"""
    
    def __init__(self):
        super().__init__()
        self.session_cookies = self._load_cookies()
    
    def _load_cookies(self):
        """Load LinkedIn cookies from file if available"""
        cookie_file = os.path.join(os.path.dirname(__file__), '../../data/linkedin_cookies.json')
        if os.path.exists(cookie_file):
            try:
                import json
                with open(cookie_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return None
    
    def _save_cookies(self, cookies):
        """Save LinkedIn cookies to file"""
        os.makedirs(os.path.join(os.path.dirname(__file__), '../../data'), exist_ok=True)
        cookie_file = os.path.join(os.path.dirname(__file__), '../../data/linkedin_cookies.json')
        try:
            import json
            with open(cookie_file, 'w') as f:
                json.dump(cookies, f)
        except:
            pass

    def scrape(self, url):
        """Scrape LinkedIn job posting"""
        print("🔗 Scraping LinkedIn job posting...")

        if 'linkedin.com' not in url:
            raise Exception("Invalid LinkedIn URL")

        # Clean the URL to avoid duplication
        url = url.strip()
        if url.count('https://www.linkedin.com/jobs/view/') > 1:
            # Extract the job ID and reconstruct clean URL
            match = re.search(r'linkedin\.com/jobs/view/(\d+)', url)
            if match:
                url = f"https://www.linkedin.com/jobs/view/{match.group(1)}"

        # Try Selenium with authentication first for better results (only if available)
        driver = None
        if SELENIUM_AVAILABLE:
            try:
                print("🔄 Trying Selenium with authentication...")
                driver = self._init_authenticated_driver()
                driver.get(url)
                
                # Wait for page load and check if login required
                time.sleep(5)
                
                # Check if we're on a login page
                if self._is_login_page(driver):
                    print("⚠️ LinkedIn requires authentication. Attempting to handle...")
                    job_data = self._scrape_limited_content(driver, url)
                    if job_data and job_data.get('description') != 'No description available':
                        return job_data
                
                # Wait for page to load with timeout
                try:
                    WebDriverWait(driver, 25).until(
                        lambda d: d.find_element(By.CSS_SELECTOR, "h1.top-card-layout__title") or
                                 d.find_element(By.CSS_SELECTOR, "h1.job-title") or
                                 d.find_element(By.CSS_SELECTOR, "h1") or
                                 d.find_element(By.CSS_SELECTOR, "div[data-test-id='job-details']")
                    )
                except Exception as wait_e:
                    print(f"⚠️ Page load timeout: {str(wait_e)}")

                # Extract job data
                job_data = self._extract_job_data(driver)
                
                # If description still not found, try requests fallback
                if not job_data.get('description') or job_data.get('description') == 'No description available':
                    print("🔄 Trying requests as fallback for description...")
                    try:
                        requests_data = self._scrape_with_requests(url)
                        if requests_data.get('description') and requests_data['description'] != 'No description available':
                            job_data['description'] = requests_data['description']
                    except:
                        pass
                
                return job_data

            except Exception as e:
                print(f"❌ Selenium scraping failed: {str(e)}")
                print("🔄 Trying requests-based fallback...")
            finally:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
        else:
            print("ℹ️ Selenium not available, using requests-based scraping...")

        # Fallback to requests (always available)
        try:
            job_data = self._scrape_with_requests(url)
            if job_data and self.validate_job_data(job_data):
                return job_data
        except:
            pass
            
        raise Exception(
            "Anti-Bot Protection Detected: LinkedIn blocks automated scanners. "
            "Please click the 'Text/Description' tab above and manually paste the job description to analyze it."
        )

    def _init_authenticated_driver(self):
        """Initialize Chrome driver with authentication options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add user agent
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = self._create_driver(chrome_options)
        
        # Execute CDP commands to hide webdriver
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        return driver
    
    def _is_login_page(self, driver):
        """Check if page requires login"""
        try:
            # Check for login/signin indicators
            page_source = driver.page_source.lower()
            login_indicators = [
                'sign in to linkedin',
                'join linkedin',
                'sign in',
                'email or phone',
                'password'
            ]
            
            # Also check for redirect to main LinkedIn page
            current_url = driver.current_url.lower()
            if 'linkedin.com/feed' in current_url or 'linkedin.com/signup' in current_url:
                return True
                
            # Check if we got redirected away from job page
            if '/jobs/view/' not in current_url:
                return True
                
            return False
        except:
            return False
    
    def _scrape_limited_content(self, driver, original_url):
        """Scrape limited content when not authenticated"""
        try:
            # Get current URL to check if we were redirected
            current_url = driver.current_url
            
            # If redirected, try to go back to original URL
            if '/jobs/view/' not in current_url:
                driver.get(original_url)
                time.sleep(5)
            
            # Try to extract what we can
            job_data = self._extract_job_data(driver)
            
            # If description is not available, try to construct from title/company
            if not job_data.get('description') or job_data.get('description') == 'No description available':
                title = job_data.get('title', '')
                company = job_data.get('company', '')
                
                if title and company:
                    job_data['description'] = f"Position: {title} at {company}. Please visit LinkedIn for full job description."
            
            return job_data
        except:
            return None
    
    def _extract_job_data(self, driver):
        """Extract job details from LinkedIn page"""
        try:
            # Job title - try multiple selectors
            title = ""
            try:
                title_elem = driver.find_element(By.CSS_SELECTOR, "h1.top-card-layout__title")
                title = title_elem.text
            except:
                try:
                    title_elem = driver.find_element(By.CSS_SELECTOR, "h1.job-title")
                    title = title_elem.text
                except:
                    try:
                        title_elem = driver.find_element(By.CSS_SELECTOR, "h1")
                        title = title_elem.text
                    except:
                        title = "Unknown Job Title"

            # Company name - try multiple selectors
            company = ""
            try:
                company_elem = driver.find_element(By.CSS_SELECTOR, "a.topcard__org-name-link")
                company = company_elem.text
            except:
                try:
                    company_elem = driver.find_element(By.CSS_SELECTOR, "span.company-name")
                    company = company_elem.text
                except:
                    try:
                        company_elem = driver.find_element(By.CSS_SELECTOR, "a.ember-view")
                        company = company_elem.text
                    except:
                        company = "Unknown Company"
            
            # Company link for domain - try multiple selectors and extract real domain
            company_domain = ""
            try:
                # Try multiple selectors for company link
                company_link_selectors = [
                    "a.topcard__org-name-link",
                    "a[data-test-id='job-details-company-name-link']",
                    "a.ember-view[href*='/company/']",
                    "a[href*='/company/']",
                    ".topcard__org-name-link a"
                ]

                company_link = ""
                for selector in company_link_selectors:
                    try:
                        link_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        href = link_elem.get_attribute("href")
                        if href and '/company/' in href:
                            company_link = href
                            break
                    except:
                        continue

                if company_link:
                    # Extract domain from company link
                    domain = self.extract_domain_from_url(company_link)

                    # If it's a LinkedIn company page, try to get the real domain from description
                    if 'linkedin.com' in domain:
                        company_domain = self._extract_real_domain_from_description(driver, company)
                    else:
                        company_domain = domain
                else:
                    # No company link found, try to extract from description
                    company_domain = self._extract_real_domain_from_description(driver, company)

            except Exception as e:
                print(f"Error extracting company domain: {str(e)}")
                # Fallback: try to extract domain from description
                company_domain = self._extract_real_domain_from_description(driver, company)

            # Final fallback: construct domain from company name
            if not company_domain and company != "Unknown Company":
                company_domain = self._construct_domain_from_company(company)
            
            # Location - try multiple selectors
            location = ""
            try:
                # Try the new selector first - look for location in top card
                location_elements = driver.find_elements(By.CSS_SELECTOR, "span.topcard__flavor--bullet")
                if len(location_elements) > 1:
                    loc_text = location_elements[1].text.strip()
                    # Clean up the location text - remove job title and company name if present
                    if "Frontend Developer Intern" in loc_text:
                        loc_text = loc_text.replace("Frontend Developer Intern", "").strip()
                    if "Hema AI" in loc_text:
                        loc_text = loc_text.replace("Hema AI", "").strip()
                    location = loc_text
                else:
                    # Try alternative top card selectors
                    try:
                        location_elem = driver.find_element(By.CSS_SELECTOR, "span.topcard__flavor[data-test-id='job-details-location']")
                        location = location_elem.text.strip()
                    except:
                        try:
                            location_elem = driver.find_element(By.CSS_SELECTOR, "span.job-details-jobs-unified-top-card__location")
                            location = location_elem.text.strip()
                        except:
                            pass
            except:
                pass

            # If still not found or contains extra text, try broader search
            if not location or location == "Not Specified" or len(location.split()) > 3:
                try:
                    # Look for any element containing location-like text
                    all_spans = driver.find_elements(By.CSS_SELECTOR, "span, div")
                    for elem in all_spans:
                        text = elem.text.strip()
                        # Look for patterns like "India", "Remote", "Mumbai, Maharashtra"
                        if len(text) < 30 and any(keyword in text.lower() for keyword in ['india', 'remote', 'mumbai', 'delhi', 'pune', 'bangalore', 'chennai', 'hyderabad']):
                            if not any(skip in text.lower() for skip in ['apply', 'save', 'share', 'report', 'ago', 'applicant', 'frontend', 'developer', 'intern', 'hema', 'ai']):
                                location = text
                                break
                except:
                    pass

            if not location:
                location = "Not Specified"
            
            # Description
            description = self._get_description(driver)
            
            # Job criteria
            criteria = self._get_job_criteria(driver)
            
            job_data = {
                'title': title,
                'company': company,
                'company_domain': company_domain,
                'location': location,
                'description': description,
                'requirements': criteria.get('requirements', ''),
                'job_type': criteria.get('job_type', ''),
                'experience_level': criteria.get('experience_level', ''),
                'salary': criteria.get('salary', ''),
                'job_portal': 'linkedin.com',
                'url': driver.current_url
            }
            
            return job_data
            
        except Exception as e:
            raise Exception(f"Failed to extract LinkedIn job data: {str(e)}")
    
    def _get_description(self, driver):
        """Extract job description from LinkedIn posting (generic - works for any job)"""
        try:
            # Give page time to fully render
            time.sleep(5)

            # Scroll to load lazy content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(2)

            # Try clicking 'Show more' to expand the full description
            try:
                show_more = driver.find_element(By.CSS_SELECTOR, "button.show-more-less-html__button--more")
                driver.execute_script("arguments[0].click();", show_more)
                time.sleep(2)
            except:
                pass

            description = ""

            # Priority 1: Most specific LinkedIn description container
            selectors = [
                "div.show-more-less-html__markup",
                "div.description__text",
                "section.description",
                "div[data-test-id='job-details-about-the-job-module']",
                "div.jobs-description__content",
                "div.jobs-description",
                "div#job-details",
            ]

            for selector in selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, selector)
                    text = elem.text.strip()
                    if len(text) > 100:
                        description = text
                        print(f"✅ Got description via '{selector}' ({len(text)} chars)")
                        break
                except:
                    continue

            # Priority 2: Look inside <main> for the longest text block
            if not description:
                try:
                    main = driver.find_element(By.TAG_NAME, "main")
                    candidates = main.find_elements(By.CSS_SELECTOR, "div, section, article")
                    best = ""
                    for elem in candidates:
                        text = elem.text.strip()
                        if len(text) > len(best) and len(text) > 200:
                            # Skip navigation/header-like blocks
                            if not any(skip in text[:100].lower() for skip in
                                       ['sign in', 'join now', 'linkedin', 'search jobs']):
                                best = text
                    if best:
                        description = best
                        print(f"✅ Got description from main content block ({len(best)} chars)")
                except:
                    pass

            # Priority 3: Full page body text as last resort
            if not description:
                try:
                    body_text = driver.find_element(By.TAG_NAME, "body").text.strip()
                    if len(body_text) > 200:
                        description = body_text[:5000]  # Cap at 5000 chars
                        print(f"⚠️ Using full body text as fallback ({len(description)} chars)")
                except:
                    pass

            return description if description else "No description available"

        except Exception as e:
            print(f"Error extracting description: {str(e)}")
            return "No description available"


    def _get_job_criteria(self, driver):
        """Extract job criteria (type, level, salary, etc.)"""
        criteria = {}
        try:
            criteria_elements = driver.find_elements(By.CSS_SELECTOR, "ul.description__job-criteria-list li")

            for elem in criteria_elements:
                text = elem.text
                if 'Employment type' in text:
                    criteria['job_type'] = text.split('\n')[1]
                elif 'Seniority level' in text:
                    criteria['experience_level'] = text.split('\n')[1]
                elif 'Salary' in text:
                    criteria['salary'] = text.split('\n')[1]
        except:
            pass

        return criteria

    def _extract_real_domain_from_description(self, driver, company_name):
        """Extract real company domain from job description and verify it"""
        try:
            # Get the full job description
            description = self._get_description(driver)

            # Look for email addresses in the description
            import re
            emails = re.findall(r'\S+@\S+', description)

            if emails:
                # Extract domain from first email
                domain = emails[0].split('@')[1].lower()

                # Verify if domain is real (not linkedin.com, gmail.com, etc.)
                if self._is_real_company_domain(domain, company_name):
                    return domain

            # Look for website URLs in description
            urls = re.findall(r'https?://(?:www\.)?([^\s/]+)', description)
            for url in urls:
                url = url.lower()
                if self._is_real_company_domain(url, company_name):
                    return url

            # Try to construct domain from company name
            company_domain = self._construct_domain_from_company(company_name)
            if company_domain and self._is_real_company_domain(company_domain, company_name):
                return company_domain

            return ""  # No valid domain found

        except:
            return ""

    def _is_real_company_domain(self, domain, company_name):
        """Check if domain is a real company domain"""
        if not domain:
            return False

        # Skip common non-company domains
        skip_domains = [
            'linkedin.com', 'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'example.com', 'test.com', 'company.com', 'business.com', 'website.com',
            'temp.com', 'fake.com', 'demo.com', 'sample.com'
        ]

        if domain in skip_domains:
            return False

        # Skip domains that are too generic
        generic_tlds = ['.xyz', '.top', '.club', '.online', '.site', '.store', '.tech']
        if any(domain.endswith(tld) for tld in generic_tlds):
            return False

        # Check if domain contains company name keywords
        company_keywords = company_name.lower().replace(' ', '').replace(',', '').replace('.', '')
        domain_clean = domain.replace('www.', '').split('.')[0]

        # Allow some common variations
        if company_keywords in domain_clean or domain_clean in company_keywords:
            return True

        # For well-known companies, allow direct matches
        known_companies = {
            'google': ['google.com', 'alphabet.com'],
            'microsoft': ['microsoft.com'],
            'amazon': ['amazon.com'],
            'apple': ['apple.com'],
            'facebook': ['facebook.com', 'meta.com'],
            'netflix': ['netflix.com'],
            'tesla': ['tesla.com'],
            'uber': ['uber.com'],
            'airbnb': ['airbnb.com']
        }

        company_lower = company_name.lower()
        for known_company, domains in known_companies.items():
            if known_company in company_lower and domain in domains:
                return True

        return False

    def _scrape_with_requests(self, url):
        """Fallback scraping method using requests and BeautifulSoup"""
        try:
            print("🔄 Using requests-based fallback scraping...")

            import os
            api_key = os.environ.get('SCRAPER_API_KEY')
            if api_key:
                from urllib.parse import urlencode
                payload = {'api_key': api_key, 'url': url, 'render_js': 'true'}
                proxy_url = 'https://api.scraperapi.com/?' + urlencode(payload)
                response = requests.get(proxy_url, timeout=45)
            else:
                response = requests.get(url, headers=headers, timeout=15)
                
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract basic job data from HTML
            job_data = {
                'title': 'Unknown Job Title',
                'company': 'Unknown Company',
                'company_domain': '',
                'location': 'Not Specified',
                'description': 'No description available',
                'requirements': '',
                'job_type': '',
                'experience_level': '',
                'salary': '',
                'job_portal': 'linkedin.com',
                'url': url
            }

            # Try to extract title
            title_selectors = [
                'h1.top-card-layout__title',
                'h1.job-title',
                'h1'
            ]
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    job_data['title'] = title_elem.get_text().strip()
                    break

            # Try to extract company
            company_selectors = [
                'a.topcard__org-name-link',
                'span.company-name',
                '.topcard__org-name-link'
            ]
            for selector in company_selectors:
                company_elem = soup.select_one(selector)
                if company_elem:
                    job_data['company'] = company_elem.get_text().strip()
                    break

            # Try to extract location
            location_selectors = [
                'span.topcard__flavor--bullet',
                '.job-details-location'
            ]
            for selector in location_selectors:
                location_elem = soup.select_one(selector)
                if location_elem:
                    job_data['location'] = location_elem.get_text().strip()
                    break

            # Try to extract description - look for JSON-LD structured data first
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                        if 'description' in data:
                            job_data['description'] = data['description']
                        if 'jobLocation' in data:
                            location = data['jobLocation']
                            if isinstance(location, dict) and 'address' in location:
                                addr = location['address']
                                if isinstance(addr, dict):
                                    city = addr.get('addressLocality', '')
                                    country = addr.get('addressCountry', '')
                                    job_data['location'] = f"{city}, {country}".strip(', ')
                        break
                except:
                    continue

            # Try to extract company domain from structured data or description
            if job_data['company'] != 'Unknown Company':
                # Look for company domain in structured data
                for script in json_ld_scripts:
                    try:
                        import json
                        data = json.loads(script.string)
                        if isinstance(data, dict) and data.get('@type') == 'Organization':
                            if 'url' in data:
                                domain = self.extract_domain_from_url(data['url'])
                                if domain and domain != 'linkedin.com':
                                    job_data['company_domain'] = domain
                                    break
                    except:
                        continue

                # If no domain from structured data, try to extract from description
                if not job_data['company_domain'] and job_data['description'] != 'No description available':
                    # Look for email addresses in description
                    emails = re.findall(r'\S+@\S+', job_data['description'])
                    if emails:
                        domain = emails[0].split('@')[1].lower()
                        if self._is_real_company_domain(domain, job_data['company']):
                            job_data['company_domain'] = domain

                    # Look for website URLs in description
                    if not job_data['company_domain']:
                        urls = re.findall(r'https?://(?:www\.)?([^\s/]+)', job_data['description'])
                        for url in urls:
                            url = url.lower()
                            if self._is_real_company_domain(url, job_data['company']):
                                job_data['company_domain'] = url
                                break

                # Final fallback: construct domain from company name
                if not job_data['company_domain']:
                    job_data['company_domain'] = self._construct_domain_from_company(job_data['company'])

            # If no structured data, try to extract from HTML with more flexible selectors
            if job_data['description'] == 'No description available':
                # Try multiple selectors for job description content
                description_selectors = [
                    'div.description__text.description__text--rich div.show-more-less-html__markup',
                    'div.description__text div.show-more-less-html__markup:not(.show-more-less-html__markup--clamp-after-5)',
                    'div.description__text div.show-more-less-html__markup.show-more-less-html__markup--clamp-after-5',
                    'section.description div.description__text.description__text--rich div.show-more-less-html__markup',
                    'div[data-test-id="job-details-about-the-job-module"]',
                    'section[data-test-id="job-details-about-the-job-module"]',
                    'div.job-details-about-the-job-module',
                    'div.job-details-jobs-unified-top-card__description-container'
                ]

                for selector in description_selectors:
                    desc_elem = soup.select_one(selector)
                    if desc_elem:
                        text = desc_elem.get_text().strip()
                        # Check for invalid/non-job content
                        invalid_patterns = [
                            'explore collaborative articles',
                            'unlocking community knowledge',
                            'experts add insights',
                            'started with the help of ai',
                            'sign in to continue',
                            'join linkedin',
                            'create an account'
                        ]
                        has_invalid = any(pattern in text.lower() for pattern in invalid_patterns)
                        
                        # More flexible validation - accept any substantial text content
                        if (len(text) > 50 and
                            not has_invalid and
                            not any(skip in text.lower() for skip in [
                                'be among the first', 'see who', 'no longer accepting', '1 day ago', 'applicants',
                                'show more jobs', 'similar jobs', 'people also viewed', 'sign in', 'join now'
                            ])):
                            job_data['description'] = text
                            print(f"✅ Found job description with selector: {selector}")
                            break

                # If still no description, try to find any substantial text in job-related containers
                if job_data['description'] == 'No description available':
                    job_containers = soup.select('div[data-test-id="job-details"], div.job-details, main')
                    for container in job_containers:
                        elements = container.select('div, p, span')
                        for elem in elements:
                            text = elem.get_text().strip()
                            if (len(text) > 100 and  # Substantial content
                                any(keyword in text.lower() for keyword in [
                                    'responsibilities', 'requirements', 'qualifications', 'experience',
                                    'skills', 'duties', 'role', 'position', 'job description',
                                    'about the job', 'about the role', 'what you\'ll do', 'what we offer',
                                    'company description', 'role description', 'position:', 'frontend', 'backend',
                                    'developer', 'intern', 'html', 'css', 'javascript', 'react', 'angular', 'vue'
                                ]) and
                                not any(skip in text.lower() for skip in [
                                    'apply', 'save', 'share', 'report', 'show more jobs',
                                    'sign in', 'sign up', 'join now', 'linkedin',
                                    'frontend developer', 'back end', 'data scientist',
                                    'wipro', 'cisco', 'unacademy', 'zee', 'bangalore', 'india',
                                    '2 weeks ago', '3 days ago', '5–8 years', 'sde ii', 'sde iii'
                                ])):
                                job_data['description'] = text
                                print("✅ Found substantial job description content in container")
                                break

            # Set default company domain if still empty
            if not job_data['company_domain']:
                job_data['company_domain'] = "Not Available"

            return job_data

        except Exception as e:
            raise Exception(f"Requests fallback scraping failed: {str(e)}")

    def _construct_domain_from_company(self, company_name):
        """Construct likely domain from company name"""
        if not company_name or company_name == "Unknown Company":
            return ""

        # Clean company name
        domain_base = company_name.lower()
        domain_base = re.sub(r'[^a-zA-Z0-9]', '', domain_base)

        # Try common domain extensions
        for ext in ['.com', '.org', '.net', '.io', '.co']:
            potential_domain = domain_base + ext
            if self._is_real_company_domain(potential_domain, company_name):
                return potential_domain

        return ""
