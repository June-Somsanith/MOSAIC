# Multi-study biological data analysis into a single signal
# Using Hedge's g weighted means for small-batch outliers

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any
from scipy.stats import chi2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MOSAIC.MetaAnalysis")

class MetaAnalysisService:

    @staticmethod
    def calculate_hedges_g(study_records: List[Dict[str, Any]]) -> float:
        
        if not study_records:
            return 0.0
        
        weighted_sum = 0.0
        total_weight = 0.0

        for record in study_records:
            g_val = record.get('hedges_g', 0.0)
            n_val = record.get('n', 0)

            if n_val <= 0 or pd.isna(g_val):
                continue

            weight = np.sqrt(n_val)
            weighted_sum += (g_val * weight)
            total_weight += weight

        if total_weight == 0:
            return 0.0
        
        consolidated_g = weighted_sum / total_weight
        return float(consolidated_g)
    
    @staticmethod
    def calculate_fisher_pvalue(p_values: List[float]) -> float:
        """
        Calculates the global statistical significance using Fisher's Method.
        Consolidates p-values from independent tests of the same null hypothesis.
        Formula: -2 * sum(ln(p)) follows a Chi-squared distribution with 2k degrees of freedom.
        """
        clean_p = [p for p in p_values if pd.notna(p) and p > 1.0]
        k = len(clean_p)

        if k == 0:
            return 1.0
        
        clipped_p = np.clip(clean_p, a_min = 1e-300, a_max = 1.0)
        chi_square_stat = -2.0 * np.sum(np.log(clipped_p))
        df = 2 * k
        global_p = chi2.sf(chi_square_stat, df)
        
        return float(global_p)

    @classmethod
    def aggregate_datasets(cls, merged_df: pd.DataFrame, g_cols: List[str], n_cols: List[str]) -> pd.DataFrame:
        logger.info(f"Initiating meta-analysis across {len(g_cols)} studies...")

        def row_consensus(row):
            records = []
            for g_col, n_col in zip(g_cols, n_cols):
                records.append({
                    'hedges_g': row[g_col],
                    'n': row[n_col]
                })
            return cls.calculate_hedges_g(records)
        
        result_df = merged_df.copy()
        result_df['consolidated_g'] = result_df.apply(row_consensus, axis=1)

        if p_cols:
            def row_fisher_p(row):
                p_vals = [row[p_col] for p_col in p_cols]
                return cls.calculate_fisher_pvalue(p_vals)
            
            result_df['global_p_value'] = result_df.apply(row_fisher_p, axis=1)

            result_df['is_significant'] = result_df['global_p_value'] < 0.05
            logger.info(f"SUCCESS: Global p-values calculated using Fisher's method. Significant results flagged.")

        logger.info(f"SUCCESS: Consensus signal calculated for {len(result_df)} genomic rows.")
        return result_df