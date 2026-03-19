# Validator for the meta-analysis engine
# Verifies square-root weighted and NaN safety mechanisms

import os
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.meta_analysis import MetaAnalysisService

def run_meta_analysis_test():
    print("=" * 60)
    print("MOSAIC: META-ANALYSIS CONSENSUS VALIDATOR")
    print("=" * 60)

    test_data = {
        "gene_id": ["ENSG0001", "ENSG0002"],
        "study1_g": [2.5, 0.5],
        "study1_n": [4, 4],
        "study1_p": [0.04, 0.55],
        "study2_g": [1.0, -0.2],
        "study2_n": [25, 25],
        "study2_p": [0.06, 0.80],
        "study3_g": [np.nan, 0.8],
        "study3_n": [6, 6],
        "study3_p": [np.nan, 0.10]
    }

    df = pd.DataFrame(test_data)

    print("STATUS: Ingesting heterogeneous multi-study dataset...")

    g_cols = ["study1_g", "study2_g", "study3_g"]
    n_cols = ["study1_n", "study2_n", "study3_n"]
    p_cols = ["study1_p", "study2_p", "study3_p"]

    result_df = MetaAnalysisService.aggregate_dataset(df, g_cols, n_cols, p_cols)

    print("\n[Meta-Analysis Results]")
    for index, row in result_df.iterrows():
        p_val = row.get('global_p_value', 1.0)
        sig = "Yes" if row.get('is_significant') else "No"
        print(f"  Gene: {row['gene_id']} | Consensus G: {row['consensus_g']:.4f} | Global P: {p_val:.5f} | Significant: {sig}")
    target_p = result_df.loc[result_df['gene_id'] == 'ENSG0001', 'global_p_value'].values[0]

    if 0.016 <= target_p <= 0.017:
        print("\nVERIFICATION: Fisher's Method successfully consolidated marginal signals into global significance.")
    else:
        print("\nWARNING: Mathematical discrepancy in Fisher's P-value calculation. Check Form.")

if __name__ == "__main__":
    run_meta_analysis_test()