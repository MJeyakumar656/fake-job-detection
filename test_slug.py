import sys
sys.path.append('.')
from src.scrapers.naukri_scraper import NaukriScraper

s = NaukriScraper()

urls = {
    "Disseminare (params)": "https://www.naukri.com/job-listings-content-presentation-content-writing-disseminare-consulting-private-limited-kolkata-mumbai-new-delhi-hyderabad-pune-chennai-bengaluru-0-to-1-years-261124501584?src=gnbOpportunities&sid=17741570880162506",
    "Disseminare (clean)": "https://www.naukri.com/job-listings-content-presentation-content-writing-disseminare-consulting-private-limited-kolkata-mumbai-new-delhi-hyderabad-pune-chennai-bengaluru-0-to-1-years-261124501584",
    "Hinduja Tech": "https://www.naukri.com/job-listings-python-developer-hinduja-tech-chennai-3-to-4-years-020326008234",
    "Acumen Tech": "https://www.naukri.com/job-listings-ui-designer-developer-acumen-technologies-private-limited-madurai-tiruppur-salem-chennai-tiruchirapalli-coimbatore-0-to-2-years-250723500453",
    "IndiaFilings": "https://www.naukri.com/job-listings-python-developer-indiafilings-chennai-0-to-3-years-020326030847",
}

with open('slug_out.txt', 'w', encoding='utf-8') as f:
    for name, url in urls.items():
        info = s._parse_url_slug(url)
        f.write(f"--- {name} ---\n")
        f.write(f"  Title:    {info['title']}\n")
        f.write(f"  Company:  {info['company']}\n")
        f.write(f"  Location: {info['location']}\n\n")
    f.write("DONE\n")

# Also print to console
with open('slug_out.txt', 'r', encoding='utf-8') as f:
    print(f.read())
