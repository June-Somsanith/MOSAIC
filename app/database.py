# Database Configuration
# Implements SQLite connection engine and session management
# Represents the systemic recover layer for long-term data storage

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database path - local SQLite for MVP
SQLALCHEMY_DATABASE_URL = "sqlite:///./mosaic_system.db"

# Create the engine
# check_same_thread = False is required for SQLite + FastAPI

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
    )

# Session Factory
SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

# Base Class for models
Base = declarative_base()

def get_db():
    """
    Metabolic dependency to yeild database sessions per request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()