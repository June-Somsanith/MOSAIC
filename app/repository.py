# Repo for CRUD operations (Create, Read, Update, Delete)
# Hanldes physiological recruitment of data from the database

from sqlalchemy.orm import Session
from app import models, schemas
from typing import List, Optional

class StudyRepository:
    """
    Manages persistence and retrieval of study metadata
    """
    @staticmethod
    def get_study(db: Session, study_id: str):
        return db.query(models.Study).filter(models.Study.id == study_id).first()
    @staticmethod
    def create_study(db: Session, study_data: dict, ai_tags: List[dict]):
        # 1. Creating study record
        db_study = models.Study(
            id = study_data["source_id"],
            title = study_data["title"],
            description = study_data["description"],
            mission = study_data["mission"]
        )
        db.add(db_study)

        # 2. Add AI Tags
        for tag in ai_tags:
            db_tag = models.AITag(
                study_id = db_study.id,
                label = tag["label"],
                confidence = tag["confidence"]
            )
            db.add(db_tag)

        db.commit()
        db.refresh(db_study)
        return db_study

class OrthologyRepository:
    """
    Manages metabolic cache for Orthology mapping
    """
    @staticmethod
    def get_mapping(db: Session, source_id: str, target_species: str):
        return db.query(models.OrthologyMap).filter(
            models.OrthologyMap.source_id == source_id,
            models.OrthologyMap.target_species == target_species
        ).first()
    
    @staticmethod
    def save_mapping(db: Session, source_id: str, target_id: str, source_species: str, target_species: str):
        db_map = models.OrthologyMap(
            source_id = source_id,
            target_id = target_id,
            source_species = source_species,
            target_species = target_species
        )
        db.add(db_map)
        db.commit()
        return db_map
