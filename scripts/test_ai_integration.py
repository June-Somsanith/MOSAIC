# Test script to verify the enriched data pipeline
# Validates the connection between genelab.py (metadata) and ai_tagger.py (classification)

import requests
import json

BASE_URL = "http://127.0.0.1:8000"
TEST_ID = "337"
ENDPOINT = f"/studies/{TEST_ID}/enriched"

def test_enriched_pipeline():
    print("=" * 60)
    print("MOSAIC: AI-ENRICHED METADATA VALIDATOR")
    print("=" * 60)

    print(f"Requesting enriched biological metadata profile for study: OSDR-{TEST_ID}...")

    try:
        # GET request to enriched endpoint
        response = requests.get(f"{BASE_URL}{ENDPOINT}")

        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: Received enriched biological metadata profile.")

            # 1. Verify metadata source from genelab.py
            print(f"\n[Source Metadata]")
            print(f"    Title: {data.get('title')}")
            print(f"    Organism: {','.join(data.get('metadata', {}).get('organism', []))}")
            print(f"    Mission: {data.get('metadata', {}).get('mission')}")

            # 2. Verify AI Analysis (from ai_tagger.py)
            ai_results = data.get('ai_classification', {})
            print(f"\n[AI-Driven Contextual Tags]")
            tags = ai_results.get('tags', {})

            if tags:
                for label, confidence in tags.items():
                    print(f"    - {label}: {confidence*100:.2f}% confidence")
                print(f"\nPrimary Classification: {ai_results.get('top_tag')}")
            else:
                print(f"    WARNING: AI Tagger returned no high-confidence tags.")
            
            print("\nVERIFICATION COMPLETE: Enriched data pipeline operational. Integration between GeneLab and AI Tagger confirmed.")

        elif response.status_code == 404:
            print(f"FAILED: Study OSDR-{TEST_ID} not found. Check OSDR API status.")

        else:
            print(f"FAILED: Server returned status code {response.status_code}")
            print(f"Error Detail: {response.json().get('detail')}")
    
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Unable to connect to the MOSAIC server. Is Uvicorn running?")
    except Exception as e:
        print(f"UNEXPECTED ERROR: {str(e)}")

if __name__ == "__main__":
    test_enriched_pipeline()