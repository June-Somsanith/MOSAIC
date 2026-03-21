# Species Alignment Service
# Normalizes heterogeneous species dataframes to a common Human Ensembl index

import pandas as pd
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.services.orthology import OrthologyService

class AlignmentService:
    @staticmethod
    async def normalize_to_human(db: Session, df: pd.DataFrame, source_species: str, id_col: str = "gene_id") -> pd.DataFrame:
        """
        Normalizes a species-specific dataframe to a common Human Ensembl index.
        Uses the SpeciesAlignment table to map source species gene IDs to human gene IDs.
        """
        if df.empty or id_col not in df.columns:
            logger.warning("Input dataframe is empty or missing the specified ID column.")
            return df
        if source_species.lower() == "human":
            logger.info("Source species is already human. No alignment needed.")
            result_df = df.copy()
            result_df['human_ortholog_id'] = result_df[id_col]
            return result_df
        
        unique_ids = df[id_col].dropna().unique().tolist()
        logger.info(f"Aligning {len(unique_ids)} unique gene IDs from {source_species} to human orthologs...")
        mapping_results = await OrthologyService.map_gene_ids(db, unique_ids, target_species="human")

        id_map = {item['source_id']: item['target_id'] for item in mapping_results if item.get('target_id')}

        result_df = df.copy()
        result_df['human_ortholog_id'] = result_df[id_col].map(id_map)

        aligned_count = result_df['human_ortholog_id'].notna().sum()
        logger.info(f"SUCCESS: Aligned {aligned_count} out of {len(unique_ids)} gene IDs to human orthologs.")

        return result_df