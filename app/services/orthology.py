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

        params = {}

        headers = {}
