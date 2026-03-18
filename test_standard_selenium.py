from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import json

url = "https://www.naukri.com/job-listings-full-stack-developer-barclays-shared-services-chennai-0-to-9-years-160326502891"

print("Setting up Standard Selenium...")
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1280,720")
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
options.add_argument("--disable-blink-features=AutomationControlled")

try:
    print("Launching regular Chrome...")
    driver = webdriver.Chrome(options=options)
    
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    print("Loading URL...")
    driver.get(url)
    
    print("Waiting for title or content...")
    time.sleep(5) # Arbitrary wait for JS
    
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
    except:
        pass
        
    print("Title:", driver.title)
    
    page_source = driver.page_source
    print("INITIAL_STATE in source:", "__INITIAL_STATE__" in page_source)
    
    driver.quit()
    print("SUCCESS")
except Exception as e:
    print("FAILED:", e)
