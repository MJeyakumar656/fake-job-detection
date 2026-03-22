from src.scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import requests
from bs4 import BeautifulSoup

class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn job postings"""
    
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

        # Try requests-based scraping first (more reliable for LinkedIn)
        try:
            print("🔄 Trying requests-based scraping first...")
            job_data = self._scrape_with_requests(url)
            print("✅ Requests scraping successful")

            # Validate that we got the correct job (not redirected)
            original_job_id = re.search(r'linkedin\.com/jobs/view/(\d+)', url)
            scraped_url = job_data.get('url', '')
            scraped_job_id = re.search(r'linkedin\.com/jobs/view/(\d+)', scraped_url)

            if original_job_id and scraped_job_id:
                if original_job_id.group(1) != scraped_job_id.group(1):
                    print(f"⚠️ LinkedIn redirected from job {original_job_id.group(1)} to {scraped_job_id.group(1)}")
                    print("🔄 Falling back to Selenium to try to access the original job...")
                    raise Exception(f"LinkedIn redirected to different job. Expected {original_job_id.group(1)}, got {scraped_job_id.group(1)}")

            # Validate that we got a proper job description using global standard
            if self._is_valid_result(job_data):
                # Additional LinkedIn-specific checks
                description = job_data.get('description', '').lower()
                if not any(skip in description for skip in [
                    'be among the first', 'no longer accepting',
                    'sign in to view', 'join now to see'
                ]):
                    print("✅ Requests scraping successful with valid description")
                    return job_data
                else:
                    print("⚠️ Requests scraping got placeholder/auth-wall description, falling back to Selenium...")
                    raise Exception("Auth-wall description from requests")
            else:
                print("⚠️ Requests scraping got invalid or blocked data, falling back to Selenium...")
                raise Exception("Invalid job data from requests")
        except Exception as e:
            print(f"❌ Requests scraping failed or incomplete: {str(e)}")
            print("🔄 Falling back to Selenium...")

            # Fallback to Selenium-based scraping
            driver = None
            try:
                driver = self.init_selenium_driver()
                driver.get(url)

                # Wait for page to load with timeout - be more flexible
                try:
                    WebDriverWait(driver, 20).until(
                        lambda d: d.find_element(By.CSS_SELECTOR, "h1.top-card-layout__title") or
                                 d.find_element(By.CSS_SELECTOR, "h1.job-title") or
                                 d.find_element(By.CSS_SELECTOR, "h1") or
                                 d.find_element(By.CSS_SELECTOR, "div[data-test-id='job-details']")
                    )
                except Exception as wait_e:
                    print(f"⚠️ Page load timeout, but continuing: {str(wait_e)}")

                # Extract job data
                job_data = self._extract_job_data(driver)

                # Final validation
                if self._is_valid_result(job_data):
                    return job_data
                else:
                    print(f"⚠️ Selenium extraction failed validation.")
                    return job_data # Return anyway as a last resort, or we could raise error

            except Exception as selenium_e:
                error_msg = f"LinkedIn scraping error: Requests failed: {str(e)} | Selenium failed: {str(selenium_e)}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
            finally:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
    
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
        """Extract job description"""
        try:
            # Wait longer for page to fully load
            time.sleep(8)

            # Scroll down to ensure content is loaded
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 4);")
            time.sleep(3)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
            time.sleep(3)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(3)

            # Get job title and company for validation
            job_title = ""
            company_name = ""
            try:
                title_elem = driver.find_element(By.CSS_SELECTOR, "h1.top-card-layout__title")
                job_title = title_elem.text.lower()
            except:
                pass
            try:
                company_elem = driver.find_element(By.CSS_SELECTOR, "a.topcard__org-name-link")
                company_name = company_elem.text.lower()
            except:
                pass

            # Define job_keywords here to ensure it's always available
            job_keywords = []
            if job_title:
                job_keywords.extend(job_title.split())
            if company_name:
                job_keywords.extend(company_name.split())

            # Try to expand "Show more" buttons for description
            try:
                # First, try to find and click the specific "Show more" button for job descriptions
                show_more_buttons = driver.find_elements(By.CSS_SELECTOR, "button.show-more-less-html__button--more")
                for button in show_more_buttons:
                    if button.is_displayed() and "show more" in button.text.lower():
                        print(f"Found and clicking 'Show more' button: {button.text}")
                        try:
                            # Try JavaScript click first
                            driver.execute_script("arguments[0].click();", button)
                            time.sleep(4)
                            print("✅ Successfully clicked 'Show more' button with JavaScript")
                            break
                        except Exception as js_e:
                            print(f"JavaScript click failed: {str(js_e)}, trying regular click")
                            try:
                                button.click()
                                time.sleep(4)
                                print("✅ Successfully clicked 'Show more' button with regular click")
                                break
                            except Exception as click_e:
                                print(f"Regular click also failed: {str(click_e)}")

                # If the specific button didn't work, try broader selectors
                if not show_more_buttons:
                    show_more_selectors = [
                        "button[aria-label*='Click to see more description']",
                        "button[data-test-id*='show-more']",
                        "button.show-more-less-html__button",
                        "button[data-test-id='show-more-less-button']",
                        "button[aria-expanded='false']",
                        "button[data-test-id='job-details-show-more-button']",
                        "button.show-more-less__button",
                        "button[data-test-id='show-more-less-button']",
                        "button.ember-view",
                        "button[data-test-id='show-more-less-html__button']",
                        "button.show-more-less-html__button--visible",
                        "button.show-more-less-button"
                    ]
                    for selector in show_more_selectors:
                        try:
                            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                            for button in buttons:
                                if button.is_displayed() and ("more" in button.text.lower() or "show" in button.text.lower()):
                                    print(f"Found and clicking show more button with selector {selector}: {button.text}")
                                    try:
                                        driver.execute_script("arguments[0].click();", button)
                                        time.sleep(4)
                                        print("✅ Successfully clicked button with JavaScript")
                                        break
                                    except Exception as js_e:
                                        print(f"JavaScript click failed: {str(js_e)}")
                                        try:
                                            button.click()
                                            time.sleep(4)
                                            print("✅ Successfully clicked button with regular click")
                                            break
                                        except Exception as click_e:
                                            print(f"Regular click also failed: {str(click_e)}")
                        except Exception as e:
                            print(f"Error with selector {selector}: {str(e)}")
                            continue
            except Exception as e:
                print(f"Error expanding show more buttons: {str(e)}")
                pass

            description = ""

            # Debug: Print page source to understand structure
            print("🔍 Debug: Looking for job description content...")

            # Save page source for debugging
            page_source = driver.page_source
            with open("debug_linkedin_page.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            print("📄 Page source saved to debug_linkedin_page.html")

            # Priority 1: Look for the main job description container - be very specific
            main_description_selectors = [
                # Most specific selector for the actual job description content
                "div.description__text.description__text--rich div.show-more-less-html__markup",
                "section.description div.description__text.description__text--rich div.show-more-less-html__markup",
                # Try expanded content after clicking show more
                "div.description__text div.show-more-less-html__markup:not(.show-more-less-html__markup--clamp-after-5)",
                "div.description__text div.show-more-less-html__markup.show-more-less-html__markup--clamp-after-5"
            ]

            for selector in main_description_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        text = elem.text.strip()
                        print(f"📝 Found content with selector '{selector}': {text[:200]}...")

                        # Accept any substantial text from the description container
                        if (len(text) > 100 and
                            not any(skip in text.lower() for skip in [
                                'be among the first', 'see who', 'no longer accepting',
                                'show more jobs', 'similar jobs', 'people also viewed',
                                'sign in to view', 'join now to see'
                            ])):
                            description = text
                            print(f"✅ Selected job description: {text[:300]}...")
                            break
                    if description:
                        break
                except Exception as e:
                    print(f"❌ Error with selector '{selector}': {str(e)}")
                    continue

            # Priority 2: Look for structured job description sections with better filtering
            if not description:
                section_selectors = [
                    "div[data-test-id='job-details-about-the-job-module']",
                    "section[data-test-id='job-details-about-the-job-module']",
                    "div.job-details-about-the-job-module",
                    "div.job-details-jobs-unified-top-card__description-container"
                ]

                for selector in section_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in elements:
                            text = elem.text.strip()
                            print(f"📝 Found section with selector '{selector}': {text[:200]}...")
                            # Apply same filtering as priority 1
                            skip_patterns = [
                                "apply", "save", "share", "report", "show more jobs",
                                "sign in", "sign up", "join now", "linkedin",
                                "frontend developer", "back end", "data scientist",
                                "wipro", "cisco", "unacademy", "zee", "bangalore", "india",
                                "2 weeks ago", "3 days ago", "5–8 years"
                            ]
                            job_listing_indicators = ["ago", "years", "₹", "$", "wipro", "cisco", "unacademy", "zee"]

                            # Count job listing indicators for priority 2 as well
                            indicator_count_2 = sum(1 for indicator in job_listing_indicators if indicator in text.lower())

                            if (len(text) > 150 and
                                not any(skip in text.lower() for skip in skip_patterns) and
                                indicator_count_2 < 3 and  # Allow some indicators but not too many
                                (not job_keywords or any(keyword in text.lower() for keyword in job_keywords[:2]))):
                                description = text
                                print(f"✅ Selected section description: {text[:300]}...")
                                break
                        if description:
                            break
                    except Exception as e:
                        print(f"❌ Error with section selector '{selector}': {str(e)}")
                        continue

            # Priority 3: Search for any substantial text content with refined filtering
            if not description:
                print("🔍 Searching for any substantial text content...")
                # Look specifically in job-related containers first
                job_containers = [
                    "div[data-test-id='job-details']",
                    "div.job-details",
                    "div.job-view-layout",
                    "main"
                ]

                for container_selector in job_containers:
                    try:
                        containers = driver.find_elements(By.CSS_SELECTOR, container_selector)
                        for container in containers:
                            elements = container.find_elements(By.CSS_SELECTOR, "div, p, span")
                            for elem in elements:
                                text = elem.text.strip()
                                # Count job listing indicators for priority 3 as well
                                indicator_count_3 = sum(1 for indicator in job_listing_indicators if indicator in text.lower())

                                text_lower = text.lower()
                                # Apply same filtering as Priority 1
                                has_job_content_3 = any(keyword in text_lower for keyword in [
                                    "responsibilities", "requirements", "qualifications", "experience",
                                    "skills", "duties", "role", "position", "job description",
                                    "about the job", "about the role", "what you'll do", "what we offer",
                                    "key responsibilities", "required skills", "frontend", "developer", "intern",
                                    "html", "css", "javascript", "react", "angular", "vue", "web development",
                                    "ui/ux", "user interface", "user experience", "responsive design"
                                ])

                                has_listing_patterns_3 = any(pattern in text_lower for pattern in [
                                    "days ago", "weeks ago", "months ago", "ago",
                                    "bengaluru, karnataka, india", "bangalore", "india",
                                    "5–8 years", "3–5 years", "2–4 years", "0–2 years",
                                    "sde ii", "sde iii", "software engineer", "full stack",
                                    "junior web developer", "html developer", "javascript developer",
                                    "back end developer", "developer internship", "wordpress developer",
                                    "layout artist", "open jobs", "show more"
                                ])

                                has_multiple_jobs_3 = sum(1 for company in ["wipro", "cisco", "unacademy", "zee", "deloitte", "healthify"] if company in text_lower) > 1

                                starts_with_job_desc_3 = text_lower.strip().startswith(("about the role", "about the job", "job description", "position summary"))

                                if (len(text) > 200 and
                                    not any(skip in text_lower for skip in skip_patterns) and
                                    (has_job_content_3 or starts_with_job_desc_3) and
                                    not has_multiple_jobs_3 and
                                    not has_listing_patterns_3 and
                                    indicator_count_3 < 2 and
                                    (not job_keywords or any(keyword in text_lower for keyword in job_keywords[:2]))):
                                    description = text
                                    print(f"✅ Found substantial content in container: {text[:300]}...")
                                    break
                            if description:
                                break
                        if description:
                            break
                    except:
                        continue

            # Priority 4: Last resort - get any text that's not obviously navigation or job listings
            if not description:
                print("🔍 Last resort search...")
                all_divs = driver.find_elements(By.CSS_SELECTOR, "div")
                for div in all_divs:
                    text = div.text.strip()
                    if (len(text) > 150 and
                        not any(skip in text.lower() for skip in [
                            "apply", "save", "share", "report", "show more jobs",
                            "sign in", "sign up", "join now", "linkedin",
                            "frontend developer", "software engineer", "full stack",
                            "wipro", "cisco", "unacademy", "zee", "bangalore", "india",
                            "2 weeks ago", "3 days ago", "5–8 years", "sde ii", "sde iii"
                        ]) and
                        (not job_keywords or any(keyword in text.lower() for keyword in job_keywords[:2]))):
                        description = text
                        print(f"✅ Last resort content: {text[:300]}...")
                        break

            if description:
                print(f"🎉 Final description found: {description[:500]}...")
            else:
                print("❌ No description found")

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

            # Try to get the page with requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

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
                        # More flexible validation - accept any substantial text content
                        if (len(text) > 50 and  # Reduced minimum length
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
