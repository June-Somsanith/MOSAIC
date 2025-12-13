import httpx
from fastapi import HTTPException
from app.schemas import StudyMetadata, ErrorResponse

OSDR_BASE_URL = "https://visualization.osdr.nasa.gov/biodata/api/v2/dataset"
# url might be https://visualization.osdr.nasa.gov/biodata/api/v2/datasets/?format=browser

async def fetch_study_metadata(source_id: str) -> StudyMetadata:
    # Ensure all ID formats are correct
    clean_id = accession_id if accession_id.startswith("OSD-") else f"OSD-{accession_id.replace('GLDS-', '')}"
    # Creating endpoint structure: /v2/dataset/{ID}/
    url = f"{OSDR_BASE_URL}/{clean_id}/"

async with httpx.AsyncClient() as client:
    try:
        response = await client.get(url, timeout = 15.0, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Study {clean_id} not found in NASA OSDR.")
        raise HTTPException(status_code=502, detail="Failed to connect to NASA OSDR API.")

raw_data = response.json()

# Transform raw data into StudyMetadata schema
# V2 API returns a complex structure that needs to be extracted at a high-level
# Structure is typically: {"OSD-123": {"metadata": {...}}}

try:
    study_root = raw_data.get(clean_id, raw_data)  # Fallback to raw_data if key not found
    info = study_root.get("metadata", {})

    # Extract relevant fields
    return StudyMetadata(
        source_id = clean_id,
        title = info.get("study title", "Unknown Title"),
        description = info.get("study description", info.get("description", "No description available")),
        organism = [info.get("organism", "Unknown Organism")],
        factors = [info.get("experimental factors", "Unspecified Factor")],
    )
except Exception as e:
    print(f"Debug Parse Error: {e}:")
    raise HTTPException(status_code = 500, detail = "Error parsing OSDR data structure")