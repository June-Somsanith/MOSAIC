# Simulating cache hit vs cache miss
# Measuring time difference between fetching data from API vs mock version from local json file

import json
import pandas as pd
import numpy as np

def test_persistance_seril():
    print("=" * 60)
    print("MOSAIC: PERSISTANCE PREPARIATION VALIDATOR")
    print("=" * 60)

    # 1. Simulating processed genomic data
    mock_data = {
        "Gene.ID": ["ENSG001", "ENSG002", "ENSG003"],
        "Sampl_A":[10.5, 20.2, 15.1],
        "Sample_B": [11.2, 19.8, 14.9]
    }

    df = pd.DataFrame(mock_data)
    print("GENERATED MOCK DF FOR SERIALIZATION TEST.")

    try:
        # 2. Convert to record format (standard for NoSQL/Firestore persistance)
        # We're using records to ensure each row is self-contined JSON object for test
        json_payload = df.to_json(orient = "records")
        parsed_data = json.loads(json_payload)

        print(f"SUCCESS: DataFrame serialized to {len(parsed_data)} records.")

        # 3. Verify Data Integrity
        first_record = parsed_data[0]
        if "Gene.ID" in first_record and first_record["Gene.ID"] == "ENSG001":
            print("VERIFICATION: Field mapping integrity confirmed.")
        else:
            print("WARNING: Data mismatch during serialization.")

        # 4. Test Deserialization (recovery path)
        recovered_df = pd.read_json(json_payload, orient = "records")
        if recovered_df.equals(df):
            print("VERIFICATION: Full round-trip prep successful.")
        else:
            print("WARNING: Round-trip check failed. Check floating point percision")
        
    except Exception as e:
        print(f"ERROR: issue during persistance prep {e}")

if __name__ == "__main__":
    test_persistance_seril()