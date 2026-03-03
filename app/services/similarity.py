# Functional similarity engine via gene ontology (GO) fingerprints
# Calculates Jaccard Similarity for genes lacking direct orthology

import httpx
import logging
import asyncio
from typing import List, Dict, Set, Optional, Any
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
        stop = stop_after_attempt(3),
        wait = wait_exponential(min = 2, max = 10),
        retry = (retry_if_exception_type(httpx.RequestError) |
        retry_if_exception_type(httpx.HTTPStatusError))
    )
    async def fetch_go_terms(client: httpx.AsyncClient, gene_id: str) -> Set[str]:
        """
        Recruits biological GO terms for a gene
        Path: /xrefs/id/:id?external_db=GO
        """
        base_id = gene_id.split('.')[0]
        url = f"{ENSEMBL_API_URL}/xrefs/id/{base_id}"
        params = {"external_db": "GO", "object_type": "gene"}
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        try:
            response = await client.get(url, params = params, headers = headers, timeout = 15.0)
            response.raise_for_status()
            data = response.json()

            go_ids = {item.get("display_id") for item in data if item.get("display_id", "").startswith("GO:")}
            logger.info(f"{gene_id} has {len(go_ids)} GO terms.")

            return go_ids
        except Exception as e:
            logger.error(f"Failed to recruit fingerprint for {gene_id}: {str(e)}")
            return set()
        
    @classmethod
    async def calculate_jaccard_score(cls, source_go: Set[str], target_go: Set[str]) -> float:
        """
        Calculates Jaccard Similarity Index. 
        Measures interscetion of biological annotations.
        """
        if not source_go or not target_go:
            return 0.0
        
        intersection = len(source_go.intersection(target_go))
        union = len(source_go.union(target_go))

        score = float(intersection / union)
        return round(score, 4)
    
    @classmethod
    async def get_functional_similarity(cls, source_id: str, potential_target_id: str) -> Dict[str, any]:
        """
        Comparison set between two genes based on functional annotations
        """
        async with httpx.AsyncClient(verify = False) as client:
            source_task = cls.fetch_go_terms(client, source_id)
            target_task = cls.fetch_go_terms(client, potential_target_id)

            source_go, target_go = await asyncio.gather(source_task, target_task)

            score = await cls.calculate_jaccard_score(source_go, target_go)

            return {
                "source_id": source_id,
                "target_id": potential_target_id,
                "similarity_score": score,
                "shared_terms_count": len(source_go.intersection(target_go)),
                "total_unique_terms": len(source_go.union(target_go)),
                "source_go_terms": list(source_go),
                "target_go_terms": list(target_go),
                "status": "calculated"
            }