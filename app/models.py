# Database models
# Defines persisted data
# implements relationships between Studies, AI Tags, and Orthology Maps

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Study(Base):
    """
    Main Study Model
    Stores core metadata called from GeneLab/OSDR
    """
    __tablename__ = "studies"

    # Use GeneLab ID as primary key for lookups

    id = Column(String, primary_key = True, index = True)
    title = Column(String, nullable = False)
    description = Column(Text, nullable = True)
    mission = Column(String, nullable = True)
    created_at = Column(DateTime(timezone = True), server_default = func.now())

    # One to many relationship with AI tags (study can have mult bio stressor tags)
    ai_tags = relationship("AITag", back_populates = "study", cascade = "all, delete-orphan")

class AITag(Base):
    """
    AI Tag Model
    Stores biological stressors identified by DistilBART model
    """
    __tablename__ = "ai_tags"

    id = Column(Integer, primary_key = True, index = True)
    study_id = Column(String, ForeignKey("studies.id"), nullable = False)
    label = Column(String, nullable = False, index = True)
    confidence = Column(Float, nullable = False)

    study = relationship("Study", back_populates = "ai_tags")

class OrthologyMap(Base):
    """
    Orthology Model
    Stores mapping between source and target species to bypass repeat API lookups...
    """
    
    __tablename__ = "ortholog_maps"

    id = Column(Integer, primary_key = True, index = True)
    source_id = Column(String, index = True, nullable = False)
    target_id = Column(String, index = True, nullable = False)
    source_species = Column(String, nullable = False)
    target_species = Column(String, nullable = False)

    # Ensureing we don't store same mapping twice
    __mapper_args__ = {"confirm_deleted_rows": False}
