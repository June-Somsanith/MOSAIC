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