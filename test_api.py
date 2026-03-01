import requests

urls = [
    "https://internshala.com/job/detail/associate-front-end-developer-remote-fresher-job-at-tripple-one-solutions1740612185",
    "https://in.indeed.com/viewjob?jk=3b39391127779b79",
    "https://www.naukri.com/job-listings-senior-software-engineer-google-inc-mumbai-delhi-ncr-bengaluru-hyderabad-pune-chennai-7-to-12-years-150223500356"
]

for url in urls:
    print(f"\n--- Testing: {url} ---")
    try:
        resp = requests.post(
            "https://jobguard-ai-api.onrender.com/api/analyze",
            json={"job_input": url, "input_type": "url"},
            timeout=120
        )
        print("Status:", resp.status_code)
        if resp.status_code != 200:
            print("Response:", resp.text[:500])
        else:
            json_data = resp.json()
            if not json_data.get('success'):
                print("API returned success=false:", json_data.get('error'))
            else:
                j = json_data['job_data']
                print(f"Success! Title: {j.get('title')}, Desc len: {len(j.get('description', ''))}")
                if 'browser does not support Javascript' in j.get('description', ''):
                    print("⚠️ JS WARNING STILL PRESENT IN OUTPUT!")
    except Exception as e:
        print("Failed to test:", e)
