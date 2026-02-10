# Systemic Primer: AI model warm-up
# Primes local cache and RAM before starting high-intensity API sessions
# Prevents timeouts during 'cold' api calls
# UPDATED: 2026-02-08

import os
import sys
import time

# path injection
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_path not in sys.path:
    sys.path.append(root_path)

from app.services.ai_tagger import AITaggerServices

def primer_session():
    print("=" * 60)
    print("MOSAIC: AI SYSTEMIC PRIMER (WARM-UP)")
    print("=" * 60)
    print("Note: This script will download and initialize the 600MB model.")
    print("This ensures your first API request doesn't stall.")
    print("-" * 60)

    start_time = time.time()

    try:
        # Recruting the classifier (this triggers the download/init)
        print("STATUS: Intitializing Neural Recruitment (Frist Rep)...")
        classifier = AITaggerServices.get_classifier()

        # Performance check
        test_text = "Metabolic analysis of liver tissue in spaceflight environment."
        print("\nSTATUS: Testing first-rep contraction (Interference)...")
        AITaggerServices.tag_text(test_text)

        end_time = time.time()
        print("\nSUCCESS: System primed in {end_time - start_time:.2f} seconds.")
        print("You can now start 'uvicorn' and run the persistence tests with zero lag.")

    except Exception as e:
        print(f"\nCRITICAL FAILURE: systemic priming failed: {e}")

if __name__ == "__main__":
    primer_session()