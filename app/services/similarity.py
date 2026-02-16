# Functional similarity engine via gene ontology (GO) fingerprints
# Calculates Jaccard Similarity for genes lacking direct orthology

import httpx
import logging
import asyncio
from typing import List, Dict, Set, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MOSAIC.Similarity")

ENSEMBL_API_URL = "https://rest.ensembl.org"

class SimilarityService:
    """
    Bio-symmetry Engine to calculate functional overlap.
    Uses GO terms to establish a similarity score between disparate genomic entities.
    """

    @staticmethod
    @retry(

    )
    async def fetch_go_terms(client: httpx.AsyncClient, gene_id: str) -> Set[str]:
        """
        Recruits biological GO terms for a gene
        Path: /xrefs/id/:id?external_db=GO
        """