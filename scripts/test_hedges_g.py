# Validator for Hedges' g correction for different sample sizes
# Verifies small-sample bias corection

import requests
import json

BASE_URL = "http://127.0.0.1:8000"
ENDPOINT = "/analytics/hedges_g"

def test_hedges_g_correction():
    print("=" * 60)
    print("MOSAIC: HEDGES' G VALIDATOR")
    print("=" * 60)

    # Simulation A gene with high fold change but small sample size
    # Flight (n=3): Mean=10.0, SD=2.0
    # Ground (n=3): Mean=5.0, SD=1.5

    test_payload = {
        "m1": 10.0,
        "m2": 5.0,
        "n1": 3,
        "n2": 3,
        "sd1": 2.0,
        "sd2": 1.5
    }
    print(f"Testing correction for small n ({test_payload['n1']}+{test_payload['n2']})...")

    try:
        response = requests.post(f"{BASE_URL}{ENDPOINT}", json=test_payload)

        if response.status_code == 200:
            data = response.json()
            hedges_g = data.get("hedges_g", 0.0)
            print(f"SUCCESS: Hedges' g calculated: {hedges_g:.4f}")
            print(f"Expected: {data.get('interpretation')}")

            if g_score < 2.5:
                print("\nVERIFICATION: Bias-correction factor detected and active.")
            else:
                print("\nWARNING: Score intensity appears uncorrected. Check Form.")
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
    except requests.exceptions.ConnectionError:
        print(f"ERROR: CNS Offline. Is uvicorn running?")
        
if __name__ == "__main__":
    test_hedges_g_correction()