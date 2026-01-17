# Does PCA logic correctly handle realistic data sizes
# Is it able to send a mock dataset to /analyze/pca

import os
import requests
import json
import random

BASE_URL = "http://127.0.0.1:8000"
ENDPOINT = "/analyze/pca"

def generate_mock_expression_data(num_genes = 50, num_samples = 6):
    # Generate mock gene expression data
    # List of Dicts (compatible with pandas DF conversion)

    data = []
    for i in range(num_genes):
        gene_entry = {"Gene.ID": f"GENE_{i:03d}"}
        for s in range(num_samples):
            # Simulate sample variance
            base_value = random.uniform(10, 1000)
            gene_entry[f"Sample_{s+1}"] = base_value + random.gauss(0, 5)
        data.append(gene_entry)
    return data

def test_pca_analysis():
    print("=" * 60)
    print("MOSAIC: ANALYTICS (PCA) VALIDATOR")
    print("=" * 60)

    # 1. Prepare Mock Data
    mock_data = generate_mock_expression_data()
    print(f"Generated mock data for {len(mock_data)} genes across 6 samples.")

    # 2. Execute Request
    try:
        response = requests.post(
            f"{BASE_URL}{ENDPOINT}",
            json = mock_data,
            params = {"n_components": 2}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: PCA calculation complete!")

            # print variance
            var = result.get("explained_variance", [])
            print(f"\n[Variance Explained]")
            print(f"PC1: {var[0]*100:.2f}%")
            print(f"PC2: {var[1]*100:.2f}%)
            
            # Print first few coordinates
            print(f"\n[Sample Coordinates (Subset)]")
            for coord in result.get("coordinates", [])[:3]:
                print(f"{coord['sample']}: PC1 = {coord['PC1']:.2f}, PC2 = {coord['PC2']:.2f}")
            
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"CONNECTION ERROR: {e}")
        
if __name__ == "__main__":
    test_pca_analysis()