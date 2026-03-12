import sys
from pprint import pprint
sys.stdout.reconfigure(encoding='utf-8')
from src.analyzer import JobAnalyzer

def main():
    # URL from the user's screenshot
    url = "https://www.naukri.com/job-listings-sap-pp-qm-functional-consultant-sigma-allied-services-gurugram-bengaluru-mumbai-all-areas-0-to-1-years-100326029611?src=drecomm_apply&sid=17733155575905936&xp=1&px=1"
    print(f"Testing URL: {url}\n")
    analyzer = JobAnalyzer()
    try:
        res = analyzer.analyze_from_url(url)
        print("\n=== FINAL RESULT ===")
        # Print keys and some values
        pprint({k: v for k, v in res.items() if k not in ['description_preview', 'red_flags_list']})
        print("\n=== RED FLAGS ===")
        pprint(res.get('red_flags_list', []))
        print("\n=== DESCRIPTION PREVIEW ===")
        print(res.get('description_preview', 'N/A'))
    except Exception as e:
        print("\n=== FATAL ERROR ===")
        print(e)

if __name__ == "__main__":
    main()
