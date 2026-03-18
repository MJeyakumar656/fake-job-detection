import subprocess
import sys

# Call Windows native curl.exe to avoid PowerShell aliases
url = "https://www.naukri.com/jobapi/v3/job/160326502891"
cmd = [
    "curl.exe", "-s", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0",
    "-H", "appid: 109", "-H", "systemid: Naukri",
    url
]

try:
    print("Running curl.exe...")
    # Use timeout of 10s
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    print("Return code:", res.returncode)
    print("Output length:", len(res.stdout))
    if len(res.stdout) > 0:
        print("Snippet:", res.stdout[:200])
except subprocess.TimeoutExpired:
    print("Timeout expired!")
