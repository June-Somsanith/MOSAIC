import httpx
from fastapi import HTTPException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.schemas import StudyMetadata
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        org_raw = metadata.get("organism")
        if org_raw:
            organisms = org_raw if isinstance(org_raw, list) else [str(org_raw)]
        
        # 2. Extract tissue types
        tissues = []
        chars = metadata.get("characteristics", {})

        target_pattern = ["tissue", "tissue type", "tissue_type", "part", "material", "source", "sample_source"]

        if isinstance(chars, dict):
            for key, value in chars.items():
                low_key = key.lower()
                if any(pattern in low_key for pattern in target_pattern):
                    if isinstance(value, list):
                        tissues.extend(value)
                    else:
                        tissues.append(str(value))
        elif isinstance(chars, str) and chars:
                tissues.append(chars)

        tissues = list(set([t for t in tissues if t]))

        # 3. Extract experimental factors
        factors = []
        factor_sources = metadata.get("experimental factors", metadata.get("experimental factors", metadata.get("factors", [])))
        if isinstance(factor_sources, list):
            for f in factor_sources:
                if isinstance(f, dict):
                    factors.append(f.get("factorName", f.get("name", str(f))))
                else:
                    factors.append(str(f))

        # 4. Extract mission (if available)
        mission_raw = metadata.get("mission_name", metadata.get("mission", "Unknown Mission"))
        if not mission_raw or (isinstance(mission_raw, str)) and mission_raw.strip() == "":
            mission = "Unknown Mission"
        elif isinstance(mission_raw, dict):
            mission = mission_raw.get("name", str(mission_raw))
        else:
            mission = str(mission_raw)

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
        logger.error(f"Debug Parse Error for {clean_id}: {str(e)}")
        raise HTTPException(status_code = 500, detail = f"Error parsing OSDR data structure: {str(e)}")