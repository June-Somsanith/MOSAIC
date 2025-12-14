# PCA/Analytics service engine

from unittest import result
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
            counts = df[numeric_cols]
            cpm = counts.div(counts.sum(axis = 0), axis = 1) * 1e6

            # 2. Log2 transform with pseudocount
            log_cpm = np.log2(cpm + 1)

            # 3. Return dataframe with normalized values
            results = df.copy()
            results[numeric_cols] = log_cpm
            return results

        return df
    
    @staticmethod
    def run_pca(df: pd.DataFrame, n_components: int = 2) -> Dict:
        # Perform PCA on the numeric columns of the dataframe
        # Dropping non-numeric columns (Gene IDs) and transpose for PCA (expects samples and features)
        numeric_data = df.select_dtypes(include = [np.number])
        # Transpose so rows become samples and columns become features (genes)
        X = numeric_data.T

        # Standardizing features (Z-score normalization)
        X_scaled = StandardScaler().fit_transfrom(X)

        # PCA computation
        pca = PCA(n_components = n_components)
        components = pca.fit(transform(X_scaled))

        # Frontend Formatting
        pca_results = []
        for i, sample_name in enumerate(numeric_df.columns):
            result.append({
                "sample": sample_name,
                "PC1": float(components[i, 0]),
                "PC2": float(components[i, 1])
            })

        return {
            "explained_variance": pca.explained_variance_ratio_.tolist(),
            "coordinates": pca_results
        }