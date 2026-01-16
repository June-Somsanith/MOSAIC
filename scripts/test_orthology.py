# main.py has /analyze/orthology -> orthologyservice.map_gene_ids
# Test to ensure the mapping between species is returning valid biological matches

import requests
import json

# API Configuration
BASE_URL = "http://127.0.0.1:8000"
ENDPOINT = "/analyze/orthology"

def test_orthology_mapping():
    print("=" * 60)
    print("MOSAIC: ORTHOLOGY MAPPING VALIDATOR")
    print("=" * 60)

    # 1. Test Case: Standard Mouse to Human Mapping
    # Mus musculus IDs: 
    test_payload = {
        "gene_ids": ["ENSMUSG00000018138", "ENSMUSG00000012396"],
        "target_species": "human"
    }

    print(f"Sending {len(test_payload['gene_ids'])} gene IDs for mapping to {test_payload['target_species']}...")

    try:
        response = requests.post(
            f"{BASE_URL}{ENDPOINT}",
            json = test_payload
        )
        
        if response.status_code == 200:
            data = response.json()
            mappings = data.get('mappings', {})

            print(f"SUCCESS: Received mapping for {data.get('mapped_gene_count', 0)} genes.")

            print("\n[Mapping Results]")
            for source, target in mappings.items():
                status = "MAPPED" if target else "NO ORTHOLOGUES FOUND"
                print(f"    Source ID: {source} -> Target ID: {target if target else 'N/A'} [{status}]")

            # Verify specific logic
            if mappings.get("ENSMUSG00000018138"):
                print("\nVERIFICATION: Primary gene (Sox2) successfully mapped.")
            else:
                print("\nWARNING: Primary gene (Sox2) failed to map. Check OrthologyService logic.")
        
        else:
            print(f"FAILED: Server returned status code {response.status_code}")
            print(f"Error Detail: {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to the MOSAIC server. Is uvicorn running?")

if __name__ == "__main__":
    test_orthology_mapping()
     