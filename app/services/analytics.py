# PCA/Analytics service engine

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Union
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from pydantic import BaseModel, Field, field_validator
import logging

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger("MOSAIC.Analytics")

class GenomicRecord(BaseModel):
    """Strict Pydantic model for individual gene records"""
    gene_id: str
    log2fc: float
    n: int = Field(..., gt = 0, description = "Sample size must be positive")

    @field_validator('gene_id')
    @classmethod
    def clean_id(cls, v):
        return v.strip().split('.')[0]
    
class AnalyticsService:
    # Consolidateing logic and methods from 'Merging_dataframes.txt' and 'AWG...R' scripts
    
    @staticmethod
    def calculate_weighted_signal(log2fc_values: List[float], n_values: List[int]) -> float:
        """
        Calculate weighted average of log2 fold change
        Uses square-root weighting method
        accounts for redution in standard error as sample size increases
        """
        if not log2fc_values or not n_values or len(log2fc_values) != len(n_values):
            logger.warning("Mismatched or empty inputs for weighted signal calculation.")
            return 0.0
        
        weights = np. sqrt(n_values)
        weighted_sum = np.sum(np.array(log2fc_values) * weights)
        total_weight = np.sum(weights)

        if total_weight == 0:
            return 0.0
        
        return float(weighted_sum / total_weight)
        
    @staticmethod
    def merge_datasets(datasets: List[pd.DataFrame], on_col: str = "Gene.ID") -> pd.DataFrame:
        # Repalce R's reduce function with pandas merge
        if not datasets:
            return pd.DataFrame()
        
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

        if numeric_cols.empty:
            logger.warning("No numeric columns found for normalization.")
            return df
        
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
    def run_pca(df: pd.DataFrame, n_components: int = 2) -> Dict[str, Any]:
        # Perform PCA on the numeric columns of the dataframe
        # Dropping non-numeric columns (Gene IDs) and transpose for PCA (expects samples and features)
        numeric_data = df.select_dtypes(include = [np.number])
        if numeric_data.empty:
            raise ValueError("No numeric data available for PCA.")
        
        # Transpose so rows become samples and columns become features (genes)
        X = numeric_data.T
        sample_names = X.index.tolist()

        # Standardizing features (Z-score normalization)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # PCA computation
        pca = PCA(n_components = n_components)
        components = pca.fit_transform(X_scaled)

        # Frontend Formatting
        pca_results = []
        for i, sample_name in enumerate(numeric_data.columns):
            pca_results.append({
                "sample": str(sample_name),
                "PC1": float(components[i, 0]),
                "PC2": float(components[i, 1]) if n_components >= 2 else 0.0
            })

        return {
            "explained_variance": pca.explained_variance_ratio_.tolist(),
            "coordinates": pca_results
        }

class FileParser:
    """Interface and implementation for multi-format standardization"""
    @staticmethod
    def parse_csv(file_path: str) -> pd.DataFrame:
        """Recrut data from CSV/TSV formats."""
        try:
            df = pd.read_csv(file_path, sep=None, engine = 'python')
            logger.info(f"SUCCESS: Ingested {len(df)} rows from {file_path}")
            return df
        except Exception as e:
            logger.error(f"FAILURE: Ingestions of {len(df)} failed: {str(e)}")
            return pd.DataFrame()
        
    @staticmethod
    def parse_fasta(file_path: str) -> List[Dict[str, str]]:
        """Extract gene headers from FASTA files for orthology recruitment."""
        sequences = []
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    if line.startswith(">"):
                        current_id = line[1:].strip().split()[0]
                        sequences.append({"gene_id": current_id})
            return sequences
        except Exception as e:
            logger.error(f"FASTA parse error: {str(e)}")
            return []