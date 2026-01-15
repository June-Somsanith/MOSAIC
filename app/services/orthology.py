# Originally we a biomaRt and Species_orthology_link files that were separate. We replaced this with a modular, automated, and steramlined architecture.
# We're creating an engine for orthology analysis that automatically translates genes between species
# We will use an API to call the Ensembl Database for gene orthology information

import httpx
import logging
import asyncio
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type # Tenacity will prevent IP address blocking due to too many requests with pandas

# configure Logging (Production Standard)
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

# Ensembl REST API base URL
ENSEMBL_API_URL = "https://rest.ensembl.org"
BATCH_SIZE = 50 # Number of genes processed in each batch, Ensebl recommends batches of 50 - 100 IDs

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
    Features: Batching, Retries, Error Handling, Async Requests.
    """

    @staticmethod
    def chunk_list(data: List[str], chunk_size: int):
        """Helper function to "chunk" our massive list of genes into smaller batches"""
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    @staticmethod
    @retry(
        stop = stop_after_attempt(3),
        wait = wait_exponential(min = 2, max = 10),
        retry = retry_if_exception_type(httpx.RequestError)
    )
    async def fetch_batch(client: httpx.AsyncClient, gene_ids: List[str], target_species: str) -> Dict[str, str]:
        
        # Adding stardized species name for Ensembl
        clean_target = SPECIES_MAP.get(target_species.lower(), target_species.lower())
        
        clean_ids = [gid.split('.')[0] for gid in gene_ids]

        url = "http://rest.ensembl.org/homology/id"
        
        payload = {
            "ids": clean_ids,
            "target_species": clean_target,
            "type": "orthologues",
            "format": "json",
            "sequence": "none" # Try without protein sequence to save bandwidth
        }



        try:
            response = await client.post(url, json = payload, headers = headers, timeout = 15.0)
            
            response.raise_for_status()
            
            full_data = response.json() # Ensembl returns JSON with a 'data' key containing a list
            data_list = full_data.get("data", [])

            # DEBUG: Log size of the data returned
            logger.info(f"Ensembl API returned results for {len(data_list)} IDs using target species: {clean_target}")

            # parse batch response
            # Ensembl returns a dictionary where keys are the Gene IDs
            batch_results = {}

            for entry in data_list:
                source_id = entry.get("id")
                original_id = next((gid for gid in gene_ids if gid.startswith(source_id)), source_id)

                homologies = entry.get("homologies", [])

                # Need deep debugging
                if not homologies:
                    logger.warning(f"DEBUG: No homologies found for {source_id}")
                    continue

                for hit in homologies:
                    # Ensembl stores target info in a nested 'target' object
                    target_info = hit.get('target', {})
                    # Standardize strings
                    hit_species = str(target_info.get('species', "")).lower().replace(" ","").replace("_","")
                    target_comp = str(clean_target).lower().replace(" ","").replace("_", "")

                    # Need deep debugging
                    logger.info(f"TRACE: {source_id} relative found: {hit_species} (looking for {target_comp})")

                    # Need deep debugging
                    logger.info(f"DEBUG: Comapring {hit_species} vs {target_comp}")

                    if hit_species == target_comp:
                        batch_results[original_id] = target_info.get('id')
                        # Need deep debugging
                        logger.info(f"DEBUG: MATCH FOUND! {source_id} -> {target_info.get('id')}")
                        break

            return batch_results
        
        except httpx.HTTPStatusError as e:
            # If Ensembl returns 400 bad requests, log it and don't retry
            if e.response.status_code == 400:
                logger.error(f"Bad request. Ensembl API error 400 for batch: {gene_ids[0]}...")
                return {}
            raise e
        
    @classmethod
    async def map_gene_ids(cls, gene_ids: List[str], target_species: str = "human") -> Dict[str, str]:
        """
        Main entry point
        Maps the batching of thousands of genes into efficient API calls. 
        """

        final_mapping = {}
        unique_gene_ids = list(set(gene_ids)) # Remove duplicates

        logger.info(f"Starting orthology mapping for {len(unique_gene_ids)} genes to {target_species}")

        async with httpx.AsyncClient() as client:
            # 1. Creating batches
            tasks = [
                cls.fetch_batch(client, batch, target_species)
                for batch in cls.chunk_list(unique_gene_ids, BATCH_SIZE)
            ]
            
            # 3. Run all batches concurrently ('gather' runs them all at the same time, so efficient time complexity)
            results = await asyncio.gather(*tasks)

            # 3. Aggregateing results
            for res in results:
                final_mapping.update(res)

        logger.info(f"Mapping completed. Total mapped genes: {len(final_mapping)}. Found {len(final_mapping)} matches.")
        return final_mapping
