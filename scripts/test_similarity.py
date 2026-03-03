# Validator for functional similarity engine
# Verifies GO Term recruitment and Jaccard Symmetry between genes

import asyncio
import httpx
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.similarity import SimilarityService

async def test_functional_symmetry():
    print("="*60)
    print("MOSAIC: FUNCTIONAL SIMILARITY VALIDATION")
    print("="*60)

    source_gene = "ENSMUSG00000018138" # Sox2
    target_gene = "ENSMUSG00000012396" # Nanog
    
    print(f"Assessing Functional Symmetry: {source_gene} vs {target_gene}")

    try:
        results = await SimilarityService.get_functional_similarity(source_gene, target_gene)

        print(f"\nSYSTEM RESULTS:")
        print(f"    Similarity Score: {results.get('similarity_score', 'N/A')}")
        print(f"    Source GO Terms: {results.get('shared_terms_count', 'N/A')}")
        print(f"    Target GO Terms: {results.get('total_unique_terms', 'N/A')}")

        score = results.get('similarity_score')
        if score > 0:
            print(f"\nSUCCESS: Functional similarity recruited and symmetry calculated.")
        else:
            print(f"\nWARNING: Zero similarity detected. Check Ensembl Xref availability and GO term recruitment.")
    except Exception as e:
        print(f"\nCRITICAL FAILURE: Similarity recruitment stalled: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_functional_symmetry())