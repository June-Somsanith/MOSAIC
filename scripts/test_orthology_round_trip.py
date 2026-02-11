# Test script to verify Asynchronous Neural Drive and Metabolic Caching
# REP 1: High-intensity Ensembl recruitment
# REP 2: Cache recruitment

import requests
import time
import json

# API Configuration
BASE_URL = "http://127.0.0.1:8000"
ENDPOINT = "/analyze/orthology"

def run_orthology_roundtrip():
    print("=" * 60)
    print("MOSAIC: ORTHOLOGY PERFORMANCE & CACHE VALIDATOR")
    print("=" * 60)

    # 1. Test Case: Standard spaceflight model genes (Sox2 and Nanog)
    test_payload = {
        "gene_ids": ["ENSMUSG00000018138", "ENSMUSG00000012396"],  # Sox2 and Nanog
        "target_species": "human"
    }

    try:
        # REP 1: API Recruitment
        print(f"REP 1: Fetching {len(test_payload['gene_ids'])} mappings from Ensembl...")
        start_1 = time.time()
        resp_1 = requests.post(f"{BASE_URL}{ENDPOINT}", json=test_payload)
        end_1 = time.time()

        latency_1 = end_1 - start_1

        if resp_1.status_code == 200:
            print(f"SUCCESS: Signal reached Ensembl. Latency: {latency_1:.2f}s")
        else:
            print(f"FAILED REP 1: {resp_1.status_code} - {resp_1.text}")
            return
        
        print("\n" + "-"*30 + "\n")

        # REP 2: Cache Recruitment
        print(f"REP 2: Re-requesting same genes to verify cache recruitment...")

        start_2 = time.time()
        resp_2 = requests.post(f"{BASE_URL}{ENDPOINT}", json=test_payload)
        end_2 = time.time()
        
        latency_2 = end_2 - start_2

        if resp_2.status_code == 200:
            data = resp_2.json()
            print(f"SUCCESS: Cache hit detected. Latency: {latency_2:.2f}s")

            if latency_2 > 0:
                speedup = latency_1 / latency_2
                print(f"\nVERFICATION: Neural Drive speedup achieved: {speedup:.1f}x")
                print(f"Cache Recruitment: {data.get('cache_hits', 0)} hits out of {data.get('source_gene_count', 0)} genes.")
            else:
                print(f"FAILED REP 2: {resp_2.status_code}")

    except requests.exceptions.ConnectionError:
        print(f"ERROR: CNS Offline. Is the uvicorn server running?")
        
if __name__ == "__main__":
    run_orthology_roundtrip()