# Test script to verify wegihted normalization
# Verify form integrity

import sys
import os
import pandas as dp
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.normalization_engine import NormalizationEngine

def test_weighted_averaging():
    print("=" * 60)
    print("MOSAIC: NORMALIZATION & WEIGHTED SIGNAL VALIDATOR")
    print("=" * 60)

    # Simulate two sudies with same gene
    # study 1: large sample set (n=25), moderate signal (log2fc=1.0)
    # study 2: small sample set (n=4), high signal (log2fc=4.0)

    log2fc = [1.0, 4.0]
    n = [25, 4]

    # Mathematical expectation:
    # Weight A = sqrt(25) = 5
    # Weight B = sqrt(4) = 2
    # Result = (1*5 + 4*2) / (5 + 2) = 13 / 7 approx 1.85

    engine = NormalizationEngine()
    result = engine.calculated_weighted_signal(log2fc, n)

    print(f"Study A (n = 25): log2FC = 1.0")
    print(f"Study B (n = 4): log2FC = 4.0")
    print("-" * 30)
    print(f"Weighted results: {result:.4f}")

    if 1.8 <= result <= 1.9:
        print("\nSUCCESS: Weighted normalization prioritized study volume correctly.")
    else:
        print("\nFAILURE: Weighted logic is not recruting sample size intensity.")

if __name__ == "__main__":
    test_weighted_averaging() 