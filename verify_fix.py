import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from src.analyzer import JobAnalyzer

def test_analyzer_failure_logic():
    analyzer = JobAnalyzer()
    
    # Mock data for a failed scrape (Naukri style)
    failed_naukri = {
        'title': 'Extraction Failed',
        'company': 'Extraction Failed',
        'description': 'Could not scrape this job. Page loaded but no content found',
        'job_portal': 'naukri.com'
    }
    
    # Mock data for a blocked scrape (Indeed style)
    blocked_indeed = {
        'title': 'Unknown Job Title',
        'company': 'Unknown Company',
        'description': "Indeed's security system blocked automation. Please paste manually.",
        'job_portal': 'indeed.com'
    }

    print("Testing Naukri failure logic...")
    result_n, _ = analyzer._analyze_job_data(failed_naukri)
    print(f"Prediction: {result_n['final_prediction']} (Expected: UNVERIFIED)")
    assert result_n['final_prediction'] == "UNVERIFIED"

    print("\nTesting Indeed block logic...")
    result_i, _ = analyzer._analyze_job_data(blocked_indeed)
    print(f"Prediction: {result_i['final_prediction']} (Expected: UNVERIFIED)")
    assert result_i['final_prediction'] == "UNVERIFIED"

    print("\n✅ Analyzer logic verification PASSED")

if __name__ == "__main__":
    try:
        test_analyzer_failure_logic()
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        sys.exit(1)
