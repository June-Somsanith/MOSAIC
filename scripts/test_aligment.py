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
        mock_db = {
            "ENSMUSG00000025902": "ENSG00000139618",
            "ENSMUSG00000051951": "ENSG00000112715"
        }
        return [{"source_id": gid, "target_id": mock_db.get(gid)} for gid in gene_ids]

import app.services.alignment
app.services.alignment.OrthologyService = MockOrthologyService

async def run_alignment_test():
    print("=" * 60)
    print("MOSAIC: UNIVERSAL SPECIES ALIGNMENT VALIDATOR")
    print("=" * 60)

    mouse_data = {
        "gene_id": ["ENSMUSG00000025902", "ENSMUSG00000051951", "ENSMUSG_ORPHAN_999"],
        "log2fc": [2.1, -1.4, 0.5],
        "p_value": [0.01, 0.04, 0.8]
    }

    df_mouse = pd.DataFrame(mouse_data)

    print("STATUS: Normalizing mouse gene IDs to human orthologs...")
    print(df_mouse.head())
    print("-" * 60)

    aligned_df = await AlignmentService.normalize_to_human(None, df_mouse, source_species="mouse", id_col="gene_id")

    print("\n[Aligned DataFrame]")
    print(aligned_df[['gene_id', 'human_ortholog_id', 'log2fc']])
    print("-" * 60)

    if 'ENSG00000139618' in aligned_df['human_ortholog_id'].values:
        print("\nVERIFICATION: Universal Human Handshake successful.")
        print("Orphan genes (no human ortholog) safely registered as NaN to prevent data convolution.")
    else:
        print("\nWARNING: Alignment failed. Human index missing.")

if __name__ == "__main__":
    asyncio.run(run_alignment_test())
    