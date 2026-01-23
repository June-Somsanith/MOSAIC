import httpx
from fastapi import HTTPException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.schemas import StudyMetadata

OSDR_BASE_URL = "https://visualization.osdr.nasa.gov/biodata/api/v2/datasets"
# url might be https://visualization.osdr.nasa.gov/biodata/api/v2/datasets/?format=browser

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=2, max=10),
    retry=(retry_if_exception_type(httpx.RequestError) |
    retry_if_exception_type(httpx.HTTPStatusError))
)
async def fetch_study_metadata(accession_id: str) -> StudyMetadata:
    # Ensure all ID formats are correct
    clean_id = accession_id if accession_id.startswith("OSD-") else f"OSD-{accession_id.replace('GLDS-', '')}"
    # Creating endpoint structure: /v2/dataset/{ID}/
    url = f"{OSDR_BASE_URL}/{clean_id}/"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout = 15.0, follow_redirects=True)
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Study {clean_id} not found in NASA OSDR.")   
        
        response.raise_for_status()

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
            organisms = org_data if isinstance(org_data, list) else [str(org_data)]
        
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
            factors = [f.get("factorName", str(f)) for f in metadata["experimental_factors"]]

        # 4. Extract mission (if available)
        mission = metadata.get("mission_name", metadata.get("mission", "Unknown Mission"))
        description_text = metadata.get("study description", metadata.get("description", "No description available"))

        return StudyMetadata(
            source_id = clean_id,
            title = metadata.get("study title", metadata.get("title", "Unknown Title")),
            description = description_text,
            organism = organisms,
            tissues = tissues,
            factors = factors,
            mission = mission
        )

    except Exception as e:
        print(f"Debug Parse Error: {e}:")
        raise HTTPException(status_code = 500, detail = f"Error parsing OSDR data structure: {str(e)}")