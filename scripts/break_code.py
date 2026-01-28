# Script to test fragility of system and points of failure

import time
import pandas as pd
import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor

def simulate_api_throttle():
    """Simulates API throttling by making rapid requests to trigger 429 errors or timeouts."""
    print("STARTING STRESS TEST: Exhausting API Connection limits")
    BASE_URL = "https://rest.ensembl.org/homology/id/ENSG0000139618" # Any example geneid

    def fire_requests(_):
        try:
            r = requests.get(BASE_URL, headers = {"Content-Type": "application/json"}, timeout = 1)
            return r.status_code
        except Exception as e:
            return str(type(e).__name__)
        
    with ThreadPoolExecutor(max_workers = 50) as executor:
        results = list(executor.map(fire_requests, range(100)))

    errors = [res for res in results if res != 200]
    print(f"FAILED: {len(errors)} requests dropped. System resilience: {100 - len(errors)}%\n")

def simulate_memory_overflow():
    # Simulates uploading a massive dataset to that exceeds the Pydantic validation buffer.
    print("STARTING STRESS TEST: Simulating Memory Overflow")
    try:
        rows = 50_000_000
        df = pd.DataFrame({
            'gene_id': np.random.randint(1000, 9999, size = rows),
            'log2fc': np.random.uniform(-5, 5, size = rows),
        })
        print(f"MEMORY USAGE: {df.memory_usage(deep = True).sum()/1024**2:2f} MB")

    except MemoryError:
        print("CRITICAL FAILURE: System ran our of RAM during ingestion.")
    print("CLEANUP: Memory released.\n")

def simulate_data_corruption():
    # Inject null values into normalization engine to test weighted-average failure.
    print("STRESS TEST: Adding NaN into Weighted Normarlization Engine...")
    data = {'n': [5, 25, 10], 'log2fc': [1.2, np.nan, -0.5]}
    df = pd.DataFrame(data)

    try:
        weighted_avg = (df['log2fc'] * np.sqrt(df['n'])).sum() / np.sqrt(df['n']).sum()
        if np.isnan(weighted_avg):
            print("FAILURE DTECTED: Weighted average resulted in NaN. Logic is vulnerable.")
        else:
            print(f"SUCCESS: Result is {weighted_avg}. Logic is resilient.")
    except Exception as e:
        print(f"CRITCIAL ERROR: {e}")

if __name__ == "__main__":
    print("STARTING MOSAIC SYSTEM FAILURE SIMULATION\n")
    simulate_api_throttle()
    simulate_data_corruption()
    simulate_memory_overflow()
    print("SIMULATION COMPLETE. Check MOSAIC Testing and Validation Log")