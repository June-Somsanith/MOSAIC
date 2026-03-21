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
    print("=" * 60)
    print("MOSAIC: 5-STUDY CONSTRAINT VALIDATOR (SAFETY RACK)")
    print("=" * 60)

    safe_payload = {"study_ids": ["OSD-137", "OSD-379", "OSD-899"]}
    print("\n[TEST 1: Safe Training Volume (3 Studies)]")
    resp1 = mock_meta_analysis_endpoint(safe_payload)
    print(f"  Count: {resp1['study_count']}")
    print(f"  Warning: {resp1['warning']}")
    if resp1['warning'] is None:
        print("  VERIFICATION: Safe volume passed without warnings. Postural integrity intact.")

    ego_payload = {"study_ids": ["OSD-1", "OSD-2", "OSD-3", "OSD-4", "OSD-5", "OSD-6", "OSD-7"]}
    print("\n[TEST 2: Convoluted Data (7 Studies)]")
    resp2 = mock_meta_analysis_endpoint(ego_payload)
    print(f"  Count: {resp2['study_count']}")
    print(f"  Warning: {resp2['warning']}")
    if resp2['warning']:
        print("  VERIFICATION: Warning successfully generated to prevent convolution.")

if __name__ == "__main__":
    run_constraint_test()