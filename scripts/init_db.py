# Initialize database and verify structural integrity

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app.models import Study, AITag, OrthologyMap

def init_db_structure():
    print("=" * 60)
    print("MOSAIC: DATABASE INITIALIZATION & STRUCTURAL CHECK")
    print("=" * 60)

    try:
        # creating all tables
        print("STATUS: BUILDING DATABASE TABLES (Studies, AI Tags, Ortholog Mpas)...")
        Base.metadata.create_all(bind = engine)

        print("SUCCESS: Database structure established.")
        print(f"PATH: {os.path.abspath('mosaic_system.db')}")

    except Exception as e:
        print(f"CRITICAL FAILURE: Could not establish database anatomy: {str(e)}")

if __name__ == "__main__":
    init_db_structure()