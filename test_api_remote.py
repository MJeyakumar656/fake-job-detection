import requests
import json

urls = [
    "https://internshala.com/job/detail/associate-front-end-developer-remote-fresher-job-at-tripple-one-solutions1740612185",
    "https://in.indeed.com/viewjob?jk=3b39391127779b79",
    "https://www.naukri.com/job-listings-senior-software-engineer-google-inc-mumbai-delhi-ncr-bengaluru-hyderabad-pune-chennai-7-to-12-years-150223500356"
]

for url in urls:
    print(f"\n--- Testing Remote: {url} ---")
    try:
        resp = requests.post(
            "https://jobguard-ai-api.onrender.com/api/analyze",
            json={"job_input": url, "input_type": "url"},
            timeout=120
        )
        print("Status:", resp.status_code)
        try:
            print("Response:", json.dumps(resp.json(), indent=2))
        except:
            print("Response Text:", resp.text)
    except Exception as e:
        print("Failed to test:", e)
