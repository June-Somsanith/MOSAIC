# Validator for the 5-Study Interpretability Warning
# Verifies that the API correctly flags 'Data Convolution' risks when n > 5

import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def mock_meta_analysis_endpoint(payload: dict) -> dict:
    study_ids = payload.get("study_ids", [])
    study_count = len(study_ids)

    if study_count == 0:
        return {"error": "No studies provided.", "status_code": 400}
    
    warning_msg = None
    if study_count > 5:
        warning_msg = (
            f"INTERPRETABILITY WARNING: Aggregating {study_count} datasets exceeds the recommended "
            "maximum of 5. Data may be convoluted, and meta-analysis results may be less reliable. Proceed with caution."
        )

    return {
        "status": "processing",
        "study_count": study_count,
        "warning": warning_msg,
        "message": "Meta-analysis initiated."
    }

def run_constraint_test():
    