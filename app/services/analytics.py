# PCA/Analytics service engine

import pandas as pd
import numpy as np
from typing import List, Dict
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

class AnalyticsService:
    # Consolidateing logic and methods from 'Merging_dataframes.txt' and 'AWG...R' scripts

    @staticmethod
    def merge_datasets(datasets: List[pd.DataFrame], on_col: str = "Gene.ID") -> pd.DataFrame:
        # Repalce R's reduce function with pandas merge
        merged_df = datasets[0]
        for df in datasets[1:]:
            merged_df = pd.merge(merged_df, df, on = on_col, how = "outer")

        return merged_df
    
    @staticmethod
    def normalize_counts(df: pd.DataFrame, method: str = "log2_cpm") -> pd.DataFrame:
        # Replaces R's log2(counts(dds, normalized = TRUE) + 4)
        # Normalize using Counts Per Million (CPM) and log2 transform
        # Assumes first column is Gene.ID and subsequent columns are numberic samples
        numeric_cols = df.select_dtypes(include = [np.number]).columns

        if method == "log2_cpm":
            # 1. Calculate CPM

            # 2. Log2 transform with pseudocount

            # 3. Return dataframe with normalized values

        return df
    
    @staticmethod
    def run_pca(df: pd.DataFrame, n_components: int = 2) -> Dict: