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
        "study2_g": [1.0, -0.2],
        "study2_n": [25, 25],
        "study3_g": [np.nan, 0.8],
        "study3_n": [6, 6]
    }

    df = pd.DataFrame(test_data)

    print("STATUS: Ingesting heterogeneous multi-study dataset...")

    g_cols = ["study1_g", "study2_g", "study3_g"]
    n_cols = ["study1_n", "study2_n", "study3_n"]

    result_df = MetaAnalysisService.aggregate_datasets(df, g_cols, n_cols)

    print("\n[Meta-Analysis Results]")
    for index, row in result_df.iterrows():
        print(f"    Gene: {row['gene_id']} | Consolidated Hedge's g = {row['consolidated_g']:.4f}")

    target_score = result_df.loc[result_df['gene_id'] == 'ENSG0001', 'consensus_g'].values[0]

    if 1.42 <= target_score <= 1.43:
        print("\nSUCCESS: Square-root weighting applied correctly. Missing data (NaN) safely skipped. Consensus score for ENSG0001 is within expected range (1.42 - 1.44).")
    else:
        print("\nFAILURE: Consensus score for ENSG0001 is outside expected range. Check weighting and NaN handling logic.")

if __name__ == "__main__":
    run_meta_analysis_test()