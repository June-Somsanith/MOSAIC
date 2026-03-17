# Multi-study biological data analysis into a single signal
# Using Hedge's g weighted means for small-batch outliers

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MOSAIC.MetaAnalysis")

class MetaAnalysis:

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

    @classmethod
    def aggregate_datasets(cls, merged_df: pd.DataFrame, g_cols: List[str], n_cols: List[str]) -> pd.DataFrame:
