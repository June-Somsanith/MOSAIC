import requests
import time
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://127.0.0.1:8000"

def test_batch_processing():
    print("\n" + "="*60)
    print("MOSAIC: API INTEGRATION AND LOADING TEST")
    print("="*60)

    test_ids = ["OSD-379", "OSD-137", "OSD-665", "OSD-824", "OSD-782"]

    payload = test_ids

    endpoint = f"{BASE_URL}/studies/batch_process"

    print(f"Sending batch request for {len(test_ids)} studies to {BASE_URL}/studies/batch_process...")

    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/studies/batch_process",
            json = payload,
            timeout = 300
        )

        # Debugging code
        print(f"DEBUG: Status Code: {response.status_code}")
        print(f"DEBUG: Raw Response Body: {response.text}")

        duration = time.time() - start_time

        if response.status_code == 200:
            data = response.json()

            if not data or data.get('count') == 0:
                print("FAILED: API returned 200, but the 'studies' list is empty.")
                print("ACTION: Check the Uvicorn terminal logs to see the 'Raw data' output.")
                return

            count = data.get('count', 0)
            studies = data.get('studies', [])

            print(f"SUCCESS: Received {data['count']} processed studies.")
            print(f"TOTAL LATENCY: {duration:.2f}s ({duration/len(test_ids):.2f}s per study)")

            if studies and len(studies) > 0:

                first_study = data['studies'][0]
                print(f"\n[Sample Verification: {test_ids[0]}]")
                print(f"    Title: {first_study.get('study title', 'N/A')[:60]}...")
                print(f"    AI Results: {first_study.get('ai_analysis', {}).get('tags')}")
            else:
                print("\nWARNING: 'studies' list is empty in the response.")

        else:
            print(f"FAILED: Status Code {response.status_code}")
            print(f"ERROR DETAIL: {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"CONNECTION ERROR: Is the FastAPI server running on {BASE_URL}?")
    except Exception as e:
        print(f"CONNECTION ERROR: An error occurred while parsing the response: {e}")

if __name__ == "__main__":
    test_batch_processing()