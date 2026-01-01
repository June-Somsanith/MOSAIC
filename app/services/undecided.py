# Creating a end-to-end batch flow
# This function calls the API once, fetches, cleans, and tags the data in one go

import asyncio
import logging
from typing import List, Dict
from app.services.genelab import fetch_study_metadata
from app.services.ai_tagger import AITaggerServices

logger = logging.getLogger(__name__)

class MOSAICBatchProcessor:
    @classmethod
    async def process_batch_studies(cls, glds_ids: List[str]) -> List[Dict]:

        logger.info(f"Starting batch processing for {len(glds_ids)} studeies.")

        # 1. Fetch metadata concurrently for all IDs
        # asyncio.gather runs all network calls concurrently

        fetch_tasks = [fetch_study_metadata(sid) for sid in glds_ids]
        metadata_results = await asyncio.gather(*fetch_tasks, return_exceptions = True)

        valid_metadata = []
        descriptions_to_tag = []

        # 2. Extract valid metadata and descriptions and prepare for tagging
        for meta in metadata_results:
            if isinstance(meta, Exception):
                logger.error(f"Error fetching metadata: {meta}")
                continue

            valid_metadata.append(meta)

            # Combine context fields for richer tagging
            # Skip calling 'tag_text' multiple times; batch all descriptions

            rich_context = f"Tissue: {', '.join(meta.tissue)}. Factors: {', '.join(meta.factors)}. Organism: {', '.join(meta.organism)}. {meta.description}"
            descriptions_to_tag.append(AITaggerServices.truncate_context(rich_context))

        # 3. Single batch AI inference

        if not descriptions_to_tag:
            return []
        
        logger.info(f"Running batch AI tagging for {len(descriptions_to_tag)} studies.")
        all_tags = AITaggerServices.tag_text(descriptions_to_tag)

        # 4. Merge AI tags with original metadata
        final_results = []
        for i, meta in enumerate(valid_metadata):
            enriched_study = meta.dict()
            enriched_study["ai_enrichment"] = all_tags[i]
            final_output.append(enriched_study)

        return final_results