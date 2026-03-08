# Originally we used biomaRt and Species_orthology_link files that were separate. 
# We replaced this with a modular, automated, and streamlined architecture.
# This engine automatically translates genes between species using the Ensembl REST API.

import httpx
import logging
import asyncio
from typing import List, Dict, Optional, Tuple, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.orm import Session

from app.repository import OrthologyRepository
from app.services.similarity import SimilarityService

# Configure Logging (Production Standard)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MOSAIC.Orthology")

# Ensembl REST API base URL
ENSEMBL_API_URL = "https://rest.ensembl.org"

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
    High-Frequency CNS Recruitment tool for cross-species gene mapping.
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
        retry=(retry_if_exception_type(httpx.RequestError) |
        retry_if_exception_type(httpx.HTTPStatusError)
        )
    )
    async def fetch_single_orthology(client: httpx.AsyncClient, gene_id: str, target_species: str) -> Tuple[str, Optional[str]]:
        """
        Fetches homology for a single gene ID using the GET endpoint.
        Path: /homology/id/:species/:id
        """
        source_species = OrthologyService.detect_source_species(gene_id)
        clean_target = SPECIES_MAP.get(target_species.lower(), target_species.lower())
        
        # Remove version suffix (e.g., .15)
        base_id = gene_id.split('.')[0]
        url = f"{ENSEMBL_API_URL}/homology/id/{base_id}"
        
        # Parameters for the GET request
        params = {
            "target_species": clean_target,
            "type": "orthologues",
            "format": "json",
            "sequence": "none"
        }
        
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

            # FIX: Ensembl homology/id/:species/:id endpoint requires GET, not POST
        response = await client.get(url, params=params, headers=headers, timeout=10.0)
                
        response.raise_for_status()
        data = response.json()
            
            # Navigate nested JSON: data -> [0] -> homologies
        try:
            homology_list = data.get("data", [{}])[0].get("homologies", [])
            
            for hit in homology_list:
                target_info = hit.get("target", {})
                hit_species = str(target_info.get("species", "")).lower().replace("_", "")
                target_comp = clean_target.lower().replace("_", "")
                
                if hit_species == target_comp:
                    target_id = target_info.get("id")
                    logger.info(f"MATCH FOUND: {gene_id} -> {target_id}")
                    return gene_id, target_id
        except (IndexError, KeyError):
            pass
            
        return gene_id, None

    @classmethod
    async def map_gene_ids(cls, db: Session, gene_ids: List[str], target_species: str = "human") -> Dict[str, str]:
        """
        Main entry point. Maps a list of genes in parallel using individual GET requests.
        """
        unique_gene_ids = list(set(gene_ids))
        final_mapping = {}
        missing_ids = []

        for gid in unique_gene_ids:
            cached_map = OrthologyRepository.get_mapping(db, gid, target_species)
            if cached_map:
                final_mapping[gid] = {
                    "target_id": cached_map.target_id,
                    "type": "direct_cache",
                    "status": "MAPPED"
                }
            else:
                missing_ids.append(gid)

        if not missing_ids:
            logger.info(f"All {len(gene_ids)} gene IDs were found in cache. No API calls needed.")
            return final_mapping
        
        logger.info(f"Fetching {len(missing_ids)} missing mappings from Ensembl")

        async with httpx.AsyncClient(verify=False) as client:
            # Create concurrent tasks for each unique gene ID
            tasks = [
                cls.fetch_single_orthology(client, gid, target_species)
                for gid in missing_ids
            ]
            
            # Execute all tasks concurrently via asyncio.gather
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, res in enumerate(results):
                gid = missing_ids[i]
                if isinstance(res, tuple) and res[1]:
                    target_id = res[1]
                    final_mapping[gid] = {
                        "target_id": target_id,
                        "type": "direct_api",
                        "status": "MAPPED"
                    }

                    try:
                        OrthologyRepository.save_mapping(db, gid, target_id, source_species, target_species)
                    except Exception as e:
                        logger.warning(f"PERSISTENCE FAILURE: {gid}: {str(e)}")
                else:
                    go_fingerprint = await SimilarityService.fetch_go_terms(client, gid)
                    final_mapping[gid] = {
                        "target_id": "No Direct Ortholog",
                        "type": "functional_fallback",
                        "status": "UNMAPPED",
                        "go_terms_count": len(go_fingerprint),
                        "functional_profile": list(go_fingerprint)[:5]  # Sample biometrics
                    }
                    
            # Build result dictionary, filtering out None targets

        logger.info(f"Mapping completed. Total mapped genes: {len([v for v in final_mapping.values() if v != 'No Ortholog Found'])}")
        return final_mapping