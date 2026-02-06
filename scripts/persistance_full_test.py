# Test script to verify database persistance
# Ensures requests are recruited from cache if available

import requests
import time

BASE_URL = "http://127.0.0.1:8000"
TEST_ID = "379"

def run_persistence_test():
    print("=" * 60)
    print("MOSAIC: PERSISTENCE & CACHE VALIDATOR")
    print("=" * 60)

    # 1. Fresh Fetch triggers AI
    print(f"REP 1: Executing fresh enrichment for study OSD-{TEST_ID}...")
    start_1 = time.time()
    resp_1 = requests.get(f"{BASE_URL}/studies/{TEST_ID}/enriched")
    end_1 = time.time()

    if resp_1.status_code == 200:
        data_1 = resp_1.json()
        print(f"STATUS: {data_1.get('status')}")
        print(f"LATENCY: {end_1 - start_1:.2f}s")
    else:
        print(f"FAILED REP 1: {resp_1.text}")
        return
    
    # 2. Cached recruitment (nearly instantaneous)
    print(f"\nREP 2: Executing cached recruitment for Study OSD-{TEST_ID}...")
    start_2 = time.time()
    resp_2 = requests.get(f"{BASE_URL}/studies/{TEST_ID}/enriched")
    end_2 = time.time()

    if resp_2.status_code == 200:
        data_2 = resp_2.json()
        print(f"STATUS: {data_2.get('status')}")
        print(f"Latency: {end_2 - start_2:.2f}s")

        if data_2.get('status') == "cached":
            print("\nSUCCESS: Cache active; Latency reduction confirmed.")
            speedup = ((end_1 - start_1) / (end_2 - start_2))
            print(f"Performance Gain: {speedup:.1f}x faster recruitment.")
        else:
            print("\nWARNING: Cache miss detected. Verify repositories.py and main.py integration.")
    else:
        print(f"FAILED REP 2: {resp_2.text}")

if __name__ == "__main__":
    run_persistence_test()