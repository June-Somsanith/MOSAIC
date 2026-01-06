from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import pandas as pd
import logging

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger("MOSAIC")

# Schemas
from app.schemas import StudyMetadata, ErrorResponse

# Services
from app.services.genelab import fetch_study_metadata
from app.services.orthology import OrthologyService
from app.services.analytics import AnalyticsService
from app.services.ai_tagger import AITaggerServices

# 1. FastAPI Application Instance
app = FastAPI(
    title = "MOSAIC Backend",
    description = "Multi-Organism Spaceflight Analysis and Integrated Comparison",
    version = "1.0.0"
)

# 2. Request AI Tagging Service
class AIRequest(BaseModel):
    text: str
    tissue: List[str] = []
    factors: List[str] = []
    organism: List[str] = []
    mission: Optional[str] = None
    labels: Optional[List[str]] = None

@app.get("/")
def read_root():
    return {"status": "active", "system": "MOSAIC"}

# 3. Data Retrieval
@app.get(
    "/studies/{glds_id}",
    response_model = StudyMetadata,
    responses = {404: {"model": ErrorResponse}}
)
# Fetch study metadata by GeneLab ID
async def get_study_metadata(glds_id: str):
    metadata = await fetch_study_metadata(glds_id)
    return metadata

# 4. Analytics and Orthology

@app.post("/analyze/orthology")
async def analyze_orthology(gene_ids: List[str], target_species: str = "human"): # Need to edit to apply any str species and to recognize species names
    mapping = await OrthologyService.map_gene_ids(gene_ids, target_species = target_species)

    return{
        "source_gene_count": len(gene_ids),
        "mapped_gene_count": len(mapping),
        "mappings": mapping
    }

@app.post("/analyze/pca")
async def perform_pca(data: List[Dict[str, Any]], n_components: int = 2):
    try:
        # 1. Convert incoming JSON list into Pandas DataFrames
        df = pd.DataFrame(data)

        # 2. Run PCA logic dfeined in Analytics Service
        pca_results = AnalyticsService.run_pca(df, n_components = n_components)
        return pca_results

    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"PCA Calculation Error: {str(e)}")

# 5. AI Engineering

@app.post("/ai/tag")
async def auto_tag_text(payload: AIRequest):
    # AI tagging that accepts description, tissue, factors, organism for smart classification
    try:
        tagging_results = AITaggerServices.generate_context_tags(
            description = payload.text,
            tissue = payload.tissue,
            factors = payload.factors,
            organism = payload.organism
        )
        return tagging_results
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"AI Error: {str(e)}")

@app.post("/studies/batch_process")
async def get_batch_studies(ids: List[str]):
    if len(ids) > 5:
        # Creating a interpretability warning
        logger.warning("Request for >5 studies. Proceeding with warning.")

    try:
        # 1. Fetch all metadata concurrently

        study_metadatas = []
        descriptions = []

        for study_id in ids:
            data_obj = await fetch_study_metadata(study_id)

            if data_obj:
                study_dict = data_obj.dict()
                study_metadatas.append(study_dict)
                descriptions.append(study_dict.get("description", ""))

        # 2. Batch AI Tagging
        if descriptions:
            ai_batch_results = AITaggerServices.tag_text(descriptions)

            # 3. Merge AI results back into the study metadata
            # Added precaution for potenial mismatch errors during AI results merging phase
            for i in range(min(len(study_metadatas), len(ai_batch_results))):
                study_metadatas[i]["ai_analysis"] = ai_batch_results[i]

        return {
            "count": len(study_metadatas),
            "studies": study_metadatas,
            "warning": "Data convolution risk" if len(ids) > 5 else None
        }
        
    except Exception as e:
        logger.error(f"Batch Processing Error: {str(e)}")
        raise HTTPException(status_code = 500, detail = str(e))
