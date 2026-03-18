import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options

url = "https://www.naukri.com/job-listings-full-stack-developer-barclays-shared-services-chennai-0-to-9-years-160326502891"

print("Setting up UC...")
chrome_options = uc.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

try:
    print("Launching UC...")
    driver = uc.Chrome(options=chrome_options)
    print("Loading URL...")
    driver.get(url)
    print("Title:", driver.title)
    driver.quit()
    print("SUCCESS")
except Exception as e:
    print("FAILED:", e)
