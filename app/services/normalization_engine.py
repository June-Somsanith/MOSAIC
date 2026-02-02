# Normalization Engine
# Implements weighted statstical algorithms to handle heterogeneous spaceflight data
# Focus on Data Integrity by weighted fold-change by sample size (n).

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, field_validator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MOSAIC.Normalization")

class GenomicRecord(BaseModel):
    """Strict Pydantic model for individual gene records"""
    gene_id: str
    log2fc: float
    n: int = Field(..., gt = 0, description = "Sample size must be positive")

    @field_validator('gene_id')
    def clean_id(cls, v):
        return v.strip().split('.')[0]

class NormalizationEngine:
    """
    Core module to solve heterogenous data problem
    Weights biological signals based on study volume (n)
    """
    @staticmethod
    def calculated_weighted_signal(log2fc_values: List[float], n_values: List[int]) -> float:
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
    def normalize_study_variance(df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply Z-score normalization within a study to make fold-changes comparable
        Formula: z = (x - mean) / std
        """
        if df.empty or 'log2fc' not in df.columns:
            return df
        
        mean = df['log2fc'].mean()
        std = df['log2fc'].std()

        if std == 0: # Trying to ensure against zero variance 
            df['normalized_score'] = 0.0
        else:
            df['nomalized_score'] = (df['log2fc'] - mean) / std

        return df

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
