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
from app.services.orthology import OrthologyService, SPECIES_MAP
from app.services.similarity import SimilarityService
from app.services.ai_tagger import AITaggerServices
from app.services.analytics import AnalyticsService

# Configure Logging (Production Standard)
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger("MOSAIC.Main")

# database anatomy initiation
Base.metadata.create_all(bind = engine)

# 1. FastAPI Application Instance
app = FastAPI(
    title = "MOSAIC BACKEND API",
    description = "Multi-Organism Spaceflight Analysis and Integrated Comparison with Persistence Layer.",
    version = "1.5.0"
)

# --- REQUEST SCHEMAS ---

# 2. Request AI Tagging Service Schema

class ComparisonRequest(BaseModel):
    gene_a: str = Field(..., description="Source Ensembl ID")
    gene_b: str = Field(..., description="Target Ensembl ID")

class AIRequest(BaseModel):
    text: str
    tissue: List[str] = [] # Aligned to singular to match StudyMetadata schema
    factors: List[str] = []
    organism: List[str] = []
    mission: Optional[str] = None
    labels: Optional[List[str]] = None

class HedgesRequest(BaseModel):
    """Request schema for Hedges' g Effect Size correction."""
    m1: float = Field(..., description="Mean of flight group")
    m2: float = Field(..., description="Mean of control group")
    n1: int = Field(..., gt=1, description="Sample size of flight group")
    n2: int = Field(..., gt=1, description="Sample size of control group")
    sd1: float = Field(..., gt=0, description="Std Dev of flight group")
    sd2: float = Field(..., gt=0, description="Std Dev of control group")

class OrthologyRequest(BaseModel):
    gene_ids: List[str]
    target_species: Optional[str] = "human"

class ComparisonRequest(BaseModel):
    """Request schema for direct functional comparison sets (GO + KEGG)."""
    gene_a: str = Field(..., description="Source Ensembl ID")
    gene_b: str = Field(..., description="Target Ensembl ID")


# --- CORE ROUTES ---

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
    """Recruits biological study metadata with integrated AI classification."""
    clean_id = glds_id if glds_id.startswith("OSD-") else f"OSD-{glds_id.replace('GLDS-', '')}"
    try:
        cached_study = StudyRepository.get_study(db, clean_id)
        if cached_study:
            return {
                "source_id": cached_study.id,
                "metadata": cached_study.__dict__,
                "ai_classification": {tag.label: tag.confidence for tag in cached_study.ai_tags},
                "status": "cached_recruitment"
            }
            
        study_metadata = await fetch_study_metadata(clean_id)
        ai_analysis = AITaggerServices.generate_context_tags(
            description=study_metadata.description,
            tissue=study_metadata.tissue,
            factors=study_metadata.factors,
            organism=study_metadata.organism
        )
        
        formatted_tags = [{"label": label, "confidence": conf} for label, conf in ai_analysis.get("tags", {}).items()]
        StudyRepository.create_study(db=db, study_data=study_metadata.dict(), ai_tags=formatted_tags)
        
        return {
            "source_id": study_metadata.source_id,
            "metadata": study_metadata.dict(),
            "ai_classification": ai_analysis,
            "status": "freshly_persisted"
        }
    except Exception as e:
        logger.error(f"Enriched Pipeline Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- ANALYTICS AND ORTHOLOGY ---

@app.post("/analyze/orthology")
async def analyze_orthology(payload: OrthologyRequest, db: Session = Depends(get_db)):
    """Maps gene IDs across species with automated functional fallback (GO + KEGG)."""
    try:
        target_species_clean = SPECIES_MAP.get(payload.target_species.lower(), payload.target_species.lower())
        final_mapping = await OrthologyService.map_gene_ids(db, payload.gene_ids, target_species_clean)
        return {
            "source_gene_count": len(payload.gene_ids),
            "mappings": final_mapping,
            "status": "complete"
        }
    except Exception as e:
        logger.error(f"Orthology Analysis Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/analyze/similarity")
async def compare_functional_similarity(payload: ComparisonRequest):
    """Direct Accessory Set: Compare functional symmetry using GO and KEGG fingerprints."""
    try:
        results = await SimilarityService.get_functional_similarity(payload.gene_a, payload.gene_b)
        return results
    except Exception as e:
        logger.error(f"Similarity Comparison Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/pca")
async def perform_pca(data: List[Dict[str, Any]], n_components: int = 2):
    """Dimensionality reduction on expression matrices."""
    try:
        df = pd.DataFrame(data)
        pca_results = AnalyticsService.run_pca(df, n_components=n_components)
        return pca_results
    except Exception as e:
        logger.error(f"PCA Calculation Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/hedges_g")
async def calculate_effect_size(payload: HedgesRequest):
    """
    Exposes the Hedges' g bias-correction logic.
    Calculates the 'true' weight of a biological signal by correcting for small n.
    """
    try:
        # Recruiting the new mathematical motor unit from AnalyticsService
        result = AnalyticsService.calculate_hedges_g(
            payload.m1, payload.m2, payload.n1, payload.n2, payload.sd1, payload.sd2
        )
        return {
            "hedges_g": result,
            "interpretation": "High Intensity" if abs(result) > 0.8 else "Moderate",
            "status": "calculated_bias_corrected"
        }
    except Exception as e:
        logger.error(f"Hedges' g Calculation Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- AI ENGINEERING ---

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