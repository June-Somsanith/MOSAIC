from fastapi import FastAPI
from app.schemas import StudyMetadata, ErrorResponse
from app.services.genelab import fetch_study_metadata
from app.services.orthology import OrthologyService
from app.services.analytics import AnalyticsService

app = FastAPI(
    title = "MOSAIC Backend",
    description = "Multi-Organism Spaceflight Analysis and Integrated Comparison",
    version = "1.0.0"
)

@app.get("/")
def read_root():
    return {"status": "active", "system": "MOSAIC"}

@app.get(
    "/studies/{glds_id}",
    response_model = StudyMetadata,
    responses = {404: {"model": ErrorResponse}}
)

async def get_study_metadata(glds_id: str):
    metadata = await fetch_study_metadata(glds_id)
    return metadata
