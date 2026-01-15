# Originally we used biomaRt and Species_orthology_link files that were separate. 
# We replaced this with a modular, automated, and streamlined architecture.
# This engine automatically translates genes between species using the Ensembl REST API.

import httpx
import logging
import asyncio
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure Logging (Production Standard)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensembl REST API base URL
ENSEMBL_API_URL = "https://rest.ensembl.org"
BATCH_SIZE = 50 

# Adding common names mapping for Ensembl Scientific nomenclature

SPECIES_MAP = {
    "human": "homo_sapiens",
    "mouse": "mus_musculus",
    "rat": "rattus_norvegicus",
    "fruitfly": "drosophila_melanogaster",
    "zebrafish": "danio_rerio",
}

class OrthologyService:
    """
    Production-grade service to handle Gene Orthology mapping.
    Features: Parallel GET requests, Species Detection, Retries, and Error Handling.
    """

    @staticmethod
    def detect_source_species(gene_id: str) -> str:
        """Detects the source species based on the Ensembl ID prefix."""
        if gene_id.startswith("ENSG"):
            return "homo_sapiens"
        elif gene_id.startswith("ENSMUSG"):
            return "mus_musculus"
        elif gene_id.startswith("ENSRNOG"):
            return "rattus_norvegicus"
        elif gene_id.startswith("FBgn"):
            return "drosophila_melanogaster"
        elif gene_id.startswith("ENSDARG"):
            return "danio_rerio"
        return "homo_sapiens"

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=2, max=10),
        retry=retry_if_exception_type(httpx.RequestError)
    )
    async def fetch_single_orthology(client: httpx.AsyncClient, gene_id: str, target_species: str) -> Optional[tuple]:
        """
        Fetches homology for a single gene ID using the GET endpoint.
        Path: /homology/id/:species/:id
        """
        source_species = OrthologyService.detect_source_species(gene_id)
        clean_target = SPECIES_MAP.get(target_species.lower(), target_species.lower())
        
        # Remove version suffix (e.g., .15)
        base_id = gene_id.split('.')[0]
        
        url = f"{ENSEMBL_API_URL}/homology/id/{source_species}/{base_id}"
        
        # Parameters for the GET request
        params = {
            "target_species": clean_target,
            "type": "orthologues",
            "format": "json",
            "sequence": "none"
        }
        
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        try:
            # FIX: Ensembl homology/id/:species/:id endpoint requires GET, not POST
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            
            if response.status_code == 400:
                return gene_id, None
                
            response.raise_for_status()
            data = response.json()
            
            # Navigate nested JSON: data -> [0] -> homologies
            homology_list = data.get("data", [{}])[0].get("homologies", [])
            
            for hit in homology_list:
                target_info = hit.get("target", {})
                hit_species = str(target_info.get("species", "")).lower().replace("_", "")
                target_comp = clean_target.lower().replace("_", "")
                
                if hit_species == target_comp:
                    target_id = target_info.get("id")
                    logger.info(f"MATCH FOUND: {gene_id} -> {target_id}")
                    return gene_id, target_id
            
            return gene_id, None
            
        except Exception as e:
            logger.warning(f"Failed to fetch orthology for {gene_id}: {str(e)}")
            return gene_id, None

    @classmethod
    async def map_gene_ids(cls, gene_ids: List[str], target_species: str = "human") -> Dict[str, str]:
        """
        Main entry point. Maps a list of genes in parallel using individual GET requests.
        """
        unique_gene_ids = list(set(gene_ids))
        logger.info(f"Starting parallel orthology mapping for {len(unique_gene_ids)} genes to {target_species}")

        async with httpx.AsyncClient() as client:
            # Create concurrent tasks for each unique gene ID
            tasks = [
                cls.fetch_single_orthology(client, gid, target_species)
                for gid in unique_gene_ids
            ]
            
            # Execute all tasks concurrently via asyncio.gather
            results = await asyncio.gather(*tasks)

            # Build result dictionary, filtering out None targets
            final_mapping = {gid: target for gid, target in results if target}

        logger.info(f"Mapping completed. Total mapped genes: {len(final_mapping)}. Found {len(final_mapping)} matches.")
        return final_mapping