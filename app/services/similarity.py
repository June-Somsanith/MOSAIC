# Functional similarity engine via gene ontology (GO) fingerprints
# Calculates Jaccard Similarity for genes lacking direct orthology

import httpx
import logging
import asyncio
from typing import List, Dict, Set, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure Logging (Production Standard)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MOSAIC.Similarity")

# Ensembl REST API base URL
ENSEMBL_API_URL = "https://rest.ensembl.org"

class SimilarityService:
    """
    Bio-symmetry Engine to calculate functional overlap.
    Recruits GO terms and KEGG pathways to establish high-intensity biological symmetry.
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
        Recruits GO terms and KEGG pathways for a gene via Deep Recruitment.
        Path: /xrefs/id/:id (Full Range of Motion)
        """
        base_id = gene_id.split('.')[0]
        url = f"{ENSEMBL_API_URL}/xrefs/id/{base_id}"
        
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        try:
            response = await client.get(url, headers = headers, timeout = 15.0)
            
            if response.status_code == 404:
                logger.warning(f"ID {gene_id} not found in Xref index.")
                return set()
            
            response.raise_for_status()
            data = response.json()

            fingerprint = set()
            go_count = 0
            kegg_count = 0
            
            for item in data:
                display_id = item.get("display_id", "")
                dbname = item.get("dbname", "").upper()
                
                # GO terms
                if display_id.startswith("GO:"):
                    fingerprint.add(display_id)
                    go_count += 1
                
                # KEGG Pathways
                if "KEGG" in dbname:
                    marker = f"KEGG:{display_id}"
                    fingerprint.add(marker)
                    kegg_count += 1
            
            logger.info(f"RECRUITMENT: {gene_id} -> {go_count} GO, {kegg_count} KEGG. Total: {len(fingerprint)}")
            return fingerprint

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
        if union == 0:
            return 0.0
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

            source_set, target_set = await asyncio.gather(source_task, target_task)

            score = await cls.calculate_jaccard_score(source_set, target_set)

            return {
                "source_id": source_id,
                "target_id": potential_target_id,
                "similarity_score": score,
                "shared_biometrics": list(source_set.intersection(target_set)),
                "source_biometric_count": len(source_set), 
                "target_biometric_count": len(target_set),
                "shared_count": len(source_set.intersection(target_set)),
                "status": "calculated_expanded"
            }