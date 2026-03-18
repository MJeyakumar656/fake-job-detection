from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import json

url = "https://www.naukri.com/job-listings-full-stack-developer-barclays-shared-services-chennai-0-to-9-years-160326502891"

options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1280,720")
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
options.add_argument("--disable-blink-features=AutomationControlled")

try:
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    driver.get(url)
    
    # Wait for the main description container
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "section.job-desc, div.dang-inner-html, div[class*='job-description']"))
    )
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Extract title
    title_elem = soup.select_one("h1")
    title = title_elem.text.strip() if title_elem else "Unknown"
    print("Title:", title)
    
    # Extract company
    company_elem = soup.select_one("div[class*='jd-header-comp-name'] a, a.company-name")
    company = company_elem.text.strip() if company_elem else "Unknown"
    print("Company:", company)
    
    # Extract description
    desc_elem = soup.select_one("section.job-desc, div.dang-inner-html, div[class*='job-description']")
    desc = desc_elem.get_text(separator='\\n').strip() if desc_elem else "Unknown"
    print("Description snippet:", desc[:200])
    
    driver.quit()
except Exception as e:
    print("FAILED:", e)
