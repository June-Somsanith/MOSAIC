import httpx
from fastapi import HTTPException
from app.schemas import StudyMetadata, ErrorResponse

OSDR_BASE_URL = "https://visualization.osdr.nasa.gov/biodata/api/v2/dataset"
# url might be https://visualization.osdr.nasa.gov/biodata/api/v2/datasets/?format=browser

async def fetch_study_metadata(accession_id: str) -> StudyMetadata:
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
        metadata = study_root.get("metadata", {})

        # Extract relevant fields

        # 1. Extract organisms
        organisms = []
        if "organism" in metadata:
            # handles both list and single string cases
            org_data = metadata["organism"]
            organisms = org_data if ininstance(org_data, list) else [str(org_data)]
        
        # 2. Extract tissue types
        tissues = []
        characteristics = metadata.get("characteristics", {})
        if "organism tissue" in characteristics:
            tissues.append(characteristics["organism tissue"])
        elif "tissue" in characteristics:
            tissues.append(characteristics["tissue"])

        # 3. Extract experimental factors
        factors = []
        if "experimental_factors" in metadata:
            factors = [f.get("factorName", str(f)) for f in metadata["expermimental_factors"]]

        # 4. Extract mission (if available)
        mission = metadata.get("mission_name", "Unknown Mission")


        return StudyMetadata(
            source_id = clean_id,
            title = metadata.get("study title", "Unknown Title"),
            description = metadata.get("study description", info.get("description", "No description available")),
            organism = organisms,
            tissues = tissues,
            factors = factors,
            mission = mission
        )

    except Exception as e:
        print(f"Debug Parse Error: {e}:")
        raise HTTPException(status_code = 500, detail = "Error parsing OSDR data structure")