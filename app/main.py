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

# Schemas
from app.schemas import StudyMetadata, ErrorResponse

# Services
from app.services.genelab import fetch_study_metadata
from app.services.orthology import OrthologyService
from app.services.analytics import AnalyticsService
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
    version = "1.1.0"
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
    return {"status": "active", "system": "MOSAIC"}

# 3. Data Retrieval & Integrated Enrichment
@app.get(
    "/studies/{glds_id}",
    response_model = StudyMetadata,
    responses = {404: {"model": ErrorResponse}}
)
# Fetch study metadata by GeneLab ID
async def get_study_metadata(glds_id: str):
    metadata = await fetch_study_metadata(glds_id)
    return metadata

@app.get("/studies/{glds_id}/enriched", response_model=dict)
async def get_enriched_study_metadata(glds_id: str, db: Session = Depends(get_db)):
    """
    Enriched metadata pipeline with metabolic caching. Checks db before triggering AI Tagging.
    """
    try:
        # 0.5. Check Cache
        cache_study = StudyRepository.get_study(db, glds_id)
        if cache_study:
            logger.info(f"CACHE HIT: Study {glds_id} recruited from persistence.")
            return{
                "source_id": cache_study.id,
                "title": cache_study.title,
                "metadata": {
                    "source_id": cache_study.id,
                    "title": cache_study.title,
                    "description": cache_study.description,
                    "mission": cache_study.mission
                },
                "ai_classification": {
                    "tags": {tag.label: tag.confidence for tag in cache_study.ai_tags},
                    "top_tag": cache_study.ai_tags[0].label if cache_study.ai_tags else None
                },
                "status": "cached_recruitment"
            }

        # 1. Ingestion Phase: genelab.py fetch
        study_metadata = await fetch_study_metadata(glds_id)

        # 2. Classification Phase: ai_tagger.py classification
        # FIX: Changed 'study_metadata.tissues' to 'study_metadata.tissue' to match schema.
        ai_analysis = AITaggerServices.generate_context_tags(
            description=study_metadata.description,
            tissue=study_metadata.tissue,
            factors=study_metadata.factors,
            organism=study_metadata.organism
        )

        # 2.5. Persistance Phase
        formatted_tags = [
            {"label": label, "confidence": conf}
            for label, conf in ai_analysis.get("tags", {}).items()
        ]

        StudyRepository.create_study(
            db = db,
            study_data = study_metadata.dict(),
            ai_tags = formatted_tags
        )

        # 3. Aggregation Phase: Merge for complete biological context
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
    Analyzes gene orthology with hybrid cache/fetch logic;
    reduces latency by avoiding redundant ensembl REST calls.
    """
    final_mapping = {}
    missing_ids = []

    # 1. Check for orthology cache
    for gid in payload.gene_ids:
        cached_map = OrthologyRepository.get_mapping(db, gid, payload.target_species)
        if cached_map:
            final_mapping[gid] = cached_map.target_id
        else:
            missing_ids.append(gid)

    # 2. Fetch missing ids from ensembl
    if missing_ids:
        logger.info(f"Recruting Ensembl for {len(missing_ids)} missing mappings.")
        new_mappings = await OrthologyService.map_gene_ids(
            gene_ids = missing_ids,
            target_species = payload.target_species
        )

        # 3. Persist new mappings to memory
        for source, target in new_mappings.items():
            source_species = OrthologyService.detect_source_species(source)
            OrthologyRepository.save_mapping(
                db, source, target, source_species, payload.target_species
            )
            final_mapping[source] = target

    return {
        "source_gene_count": len(payload.gene_ids),
        "mapped_gene_count": len(final_mapping),
        "mappings": final_mapping,
        "cache_hits": len(payload.gene_ids) - len(missing_ids)
    }

@app.post("/analyze/pca")
async def perform_pca(data: List[Dict[str, Any]], n_components: int = 2):
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
    # AI tagging that accepts description, tissue, factors, organism for smart classification
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