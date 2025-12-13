# Building a simple data schema using Pydantic
from pydantic import BaseModel, Field
from typing import List, Optional

class StudyMetadata(BaseModel):
    source_id: str = Field(..., description="The ID from Genelab or other exteranal source (e.g., GLDS-123)")
    title: str
    organism: List[str]
    factors: List[str] = Field(default=[], description="Experimental factors (e.g., Spaceflight, Radiation, Gravitational factor, etc.)")
    description: Optional[str] = None

# Prep for phase 2: AI Engineering (NLP and or NER tagging)

ai_tags = Optional[List[str]] = Field(default=None, description="NLP-derived tags")")

class ErrorResponse(BaseModel):
    error: str
    detail: str
