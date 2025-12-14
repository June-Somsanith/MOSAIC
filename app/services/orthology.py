# Originally we a biomaRt and Species_orthology_link files that were separate. We replaced this with a modular, automated, and steramlined architecture.
# We're creating an engine for orthology analysis that automatically translates genes between species
# We will use an API to call the Ensembl Database for gene orthology information

import httpx
import logging
import asyncio
from typing import List, Dict, Optional
import tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type # Tenacity will prevent IP address blocking due to too many requests with pandas

# configure Logging (Production Standard)
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

# Ensembl REST API base URL
ENSEMBL_API_URL = "https://rest.ensembl.org"
BATCH_SIZE = 100 # Number of genes processed in each batch, Ensebl recommends batches of 50 - 100 IDs

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
        stop = stop_after_attempt(5),
        wait = wait_exponential(multiplier = 1, min = 2, max = 10),
        retry = retry_if_exception_type(httpx.RequestError)
    )
    async def fetch_batch(client: httpx.AsyncClient, gene_ids: List[str], target_species: str) -> Dict[str, str]:
        url = f"{ENSEMBL_API_URL}/homology/id"
        
        payload = {"ids": gene_ids}

        params = {
            "target_species": target_species,
            "type": "orthologues",
            "format": "json"
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = await client.post(url, json = payload, params = params, headers = headers, timeout = 10.0)
            response.raise_for_status()
            data = response.json()

            # parse batch response
            # Ensembl returns a dictionary where keys are the Gene IDs
            batch_results = {}

            for sorce_id, results_obj in data.items():
                if not result_obj:
                    continue

                homologies = result_obj[0].get("homologies", [])
                for hit in homologies:
                    # Double-checking target species
                    if hit['target_species'] == target_species and hit['is_tree_compliant'] == 1:
                        batch_results[sorce_id] = hit['target']['id']
                        # Stop after first high-confidence orthologue match to keep 1:1 maapping, this can be changed later
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
            task = []

            # 1. Creating batches
            for batch in cls.chunk_list(unique_gene_ids, BATCH_SIZE):
                # 2. Scheduling batch requests
                task.append(cls.fetch_batch(client, batch, target_species))

            # 3. Run all batches concurrently ('gather' runs them all at the same time, so efficient time complexity)
            results = await asyncio.gather(*task, return_exceptions = True)

            # 4. Aggregateing results
            for res in results:
                if ininstance(res, dict):
                    final_mapping.update(res)
                elif ininstance(res, Exception):
                    logger.error(f"Batch failed error: {str(res)}")

        logger.info(f"Mapping completed. Total mapped genes: {len(final_mapping)}. Found {len(final_mapping)} matches.")
        return final_mapping
