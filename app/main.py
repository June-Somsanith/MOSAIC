from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import pandas as pd
import logging

# Database/Persistence Recruitment
from app.database import engine, Base, get_db
from app.models import Study, AITag, OrthologyMap
from app.repository import StudyRepository, OrthologyRepository
from app.schemas import StudyMetadata, ErrorResponse

# Services
from app.services.genelab import fetch_study_metadata
from app.services.orthology import SPECIES_MAP, OrthologyService
from app.services.analytics import AnalyticsService, FileParser
from app.services.ai_tagger import AITaggerServices

# Configure Logging (Production Standard)
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger("MOSAIC")

# database anatomy initiation
Base.metadata.create_all(bind = engine)

# 1. FastAPI Application Instance
app = FastAPI(
    title = "MOSAIC BACKEND API",
    description = "Multi-Organism Spaceflight Analysis and Integrated Comparison with Persistence Layer.",
    version = "1.1.1"
)

# 2. Request AI Tagging Service Schema
class AIRequest(BaseModel):
    text: str
    tissue: List[str] = [] # Aligned to singular to match StudyMetadata schema
    factors: List[str] = []
    organism: List[str] = []
    mission: Optional[str] = None
    labels: Optional[List[str]] = None

class OrthologyRequest(BaseModel):
    gene_ids: List[str]
    target_species: Optional[str] = "human"

@app.get("/")
def read_root():
    return {"status": "active", "system": "MOSAIC", "persistence": "Active (SQLite)"}

@app.get(
    "/studies/{glds_id}",
    response_model=StudyMetadata,
    responses={404: {"model": ErrorResponse}}
)
async def get_study_metadata(glds_id: str):
    """Simple metadata recruitment from NASA OSDR."""
    metadata = await fetch_study_metadata(glds_id)
    return metadata

@app.get("/studies/{glds_id}/enriched", response_model=dict)
async def get_enriched_study_metadata(glds_id: str, db: Session = Depends(get_db)):
    """
    Orchestrates the 'Enriched' metadata pipeline with ID Normalization.
    Ensures 'Postural Integrity' by checking for OSD-prefixed IDs in the cache.
    """
    # 1. ID NORMALIZATION (The Postural Check)
    # Ensures raw inputs like '379' match the persisted 'OSD-379' format.
    clean_id = glds_id if glds_id.startswith("OSD-") else f"OSD-{glds_id.replace('GLDS-', '')}"

    try:
        # 2. Check Cache (Recruitment from Muscle Memory)
        # Using clean_id here is critical to avoid IntegrityErrors during the Save phase.
        cached_study = StudyRepository.get_study(db, clean_id)
        if cached_study:
            logger.info(f"CACHE HIT: Study {clean_id} recruited from persistence.")
            return {
                "source_id": cached_study.id,
                "title": cached_study.title,
                "metadata": {
                    "source_id": cached_study.id,
                    "title": cached_study.title,
                    "description": cached_study.description,
                    "mission": cached_study.mission
                },
                "ai_classification": {
                    "tags": {tag.label: tag.confidence for tag in cached_study.ai_tags},
                    "top_tag": cached_study.ai_tags[0].label if cached_study.ai_tags else None
                },
                "status": "cached_recruitment"
            }

        # 3. Ingestion Phase: Fetch from NASA OSDR
        study_metadata = await fetch_study_metadata(clean_id)

        # 4. Enrichment Phase: AI-Driven Classification
        ai_analysis = AITaggerServices.generate_context_tags(
            description=study_metadata.description,
            tissue=study_metadata.tissue,
            factors=study_metadata.factors,
            organism=study_metadata.organism
        )

        # 5. Persistence Phase (Saving the Gains)
        formatted_tags = [
            {"label": label, "confidence": conf} 
            for label, conf in ai_analysis.get("tags", {}).items()
        ]
        
        StudyRepository.create_study(
            db=db,
            study_data=study_metadata.dict(),
            ai_tags=formatted_tags
        )

        return {
            "source_id": study_metadata.source_id,
            "title": study_metadata.title,
            "metadata": study_metadata.dict(),
            "ai_classification": ai_analysis,
            "status": "freshly_persisted"
        }
    
    except Exception as e:
        logger.error(f"Enriched Data Pipeline Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline Error: {str(e)}")

# 4. Analytics and Orthology

@app.post("/analyze/orthology")
async def analyze_orthology(payload: OrthologyRequest, db: Session = Depends(get_db)):
    """
    Analyzes gene orthology with Hybrid Cache/Fetch logic.
    Reduces Latency by avoiding redundant Ensembl REST calls.
    """
    try:
        # 1. Check Orthology Cache
        target_species_clean = SPECIES_MAP.get(payload.target_species.lower(), payload.target_species.lower())

        hits = 0
        for gid in payload.gene_ids:
            if OrthologyRepository.get_mapping(db, gid, target_species_clean):
                hits += 1

    # 2. Fetch Missing IDs from Ensembl
        final_mapping = await OrthologyService.map_gene_ids(
            db,
            payload.gene_ids,
            target_species_clean
        )

        if hits == 0:
            logger.info(f"Processing {len(payload.gene_ids)} genes with no cache hits. Full Ensembl recruitment.")
        else:
            logger.info(f"Processing {len(payload.gene_ids)} genes with {hits} cache hits. Partial Ensembl recruitment.")

        return {
            "source_gene_count": len(payload.gene_ids),
            "mapped_gene_count": len([v for v in final_mapping.values() if v != "No Ortholog Found"]),
            "mappings": final_mapping,
            "cache_hits": hits,
            "status": "complete"
        }
    except Exception as e:
        logger.error(f"Orthology Analysis Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Orthology Error: {str(e)}")

@app.post("/analyze/pca")
async def perform_pca(data: List[Dict[str, Any]], n_components: int = 2):
    """
    Dimensionality reduction on expression matrices
    """
    try:
        # 1. Convert incoming JSON list into Pandas DataFrames
        df = pd.DataFrame(data)

        # 2. Run PCA logic defined in Analytics Service
        pca_results = AnalyticsService.run_pca(df, n_components = n_components)
        return pca_results

    except Exception as e:
        logger.error(f"PCA Calculation Failed: {str(e)}")
        raise HTTPException(status_code = 500, detail = f"PCA Calculation Error: {str(e)}")

# 5. AI Engineering

@app.post("/ai/tag")
async def auto_tag_text(payload: AIRequest):
    """
    Direct Zero-shot classification for arbitrary biological text.
    """
    try:
        tagging_results = AITaggerServices.generate_context_tags(
            description = payload.text,
            tissue = payload.tissue, # Aligned to singular
            factors = payload.factors,
            organism = payload.organism
        )
        return tagging_results
    except Exception as e:
        logger.error(f"AI Tagging Error: {str(e)}")
        raise HTTPException(status_code = 500, detail = f"AI Error: {str(e)}")

@app.post("/studies/batch_process")
async def get_batch_studies(ids: List[str]):
    """High-volume batch processing for multiple study IDs."""
    if len(ids) > 5:
        # Creating an interpretability warning
        logger.warning("Request for >5 studies. Proceeding with warning.")

    study_metadatas = []
    descriptions = []
        
    for study_id in ids:
        try:
            # 1. Fetch all metadata concurrently
            data_obj = await fetch_study_metadata(study_id)

            if data_obj:
                study_dict = data_obj.dict()
                study_metadatas.append(study_dict)
                descriptions.append(study_dict.get("description", ""))
        
        except Exception as e:
            logger.error(f"Skipping {study_id} due to fetch error: {str(e)}")
            continue

    # 2. Batch AI Tagging
    if descriptions:
        try:
            ai_batch_results = AITaggerServices.tag_text(descriptions)

            # Added to make sure results are in list for merge loop
            if isinstance(ai_batch_results, dict):
                ai_batch_results = [ai_batch_results]

            # 3. Merge AI results back into the study metadata
            for i in range(min(len(study_metadatas), len(ai_batch_results))):
                study_metadatas[i]["ai_classification"] = ai_batch_results[i]
            
        except Exception as e:
            logger.error(f"AI Tagging failed for batch: {str(e)}")

    return {
        "count": len(study_metadatas),
        "studies": study_metadatas,
        "batch_status": "complete",
        "warning": "Data convolution risk" if len(ids) > 5 else None
    }