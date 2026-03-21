# Validator for the alignment service engine
# Verifies species normalization and ortholog mapping integrity

import os
import sys
import pandas as pd
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.alignment import AlignmentService

class MockOrthologyService:
    @staticmethod
    async def map_gene_ids(db, gene_ids, target_species):
        mock_db = [
            {"source_id": "ENSMUSG00000000001", "target_id": "ENSG00000000001"},
            {"source_id": "ENSMUSG00000000028", "target_id": "ENSG00000000028"},
        ]
        return [{"source_id": gid, "target_id": mock_db.get(gid)} for gid in gene_ids]

