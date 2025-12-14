# Building a simple data schema using Pydantic
from pydantic import BaseModel, Field
from typing import List, Optional

class StudyMetadata(BaseModel):
    source_id: str = Field(..., description = "The ID from Genelab or other exteranal source (e.g., GLDS-123)")
    title: str
    description: Optional[str] = None

    # Fields to enrich AI content tagging
    organism: List[str] = Field(default_factory = list)
    tisuse: List[str] = Field(default_factory = list, description = "Tissue types involved in the study (e.g., Liver, Eye, Root, etc.)")
    factors: List[str] = Field(default=[], description="Experimental factors (e.g., Spaceflight, Radiation, Gravitational factor, etc.)")
    mission: Optional[str] = None
    

class ErrorResponse(BaseModel):
    error: str
    detail: str
