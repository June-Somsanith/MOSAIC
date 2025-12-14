# 1. Creating the orthologous analysis code

# 2. Cleaning up data/code

Originally we had a collection of different manual scripts. We needed to combine and condense these scripts to run automatically and streamline the logic into a servicable application.

We created the orthology.py file to stand in place of our BiomaRt and Species_orthology_link scripts. This new script is able to handle gene ID mapping.

The analytics.py combined our Merging_dataframes.txt and AWG_transcriptomics_sorting_&adapted_IDEP9.3_code.R into a comprehensive script that could handle the merging of datasets along with normalization and PCA in one.


# 3. Phase 1: Create the application

### 1. Installing dependencies

We first listed our dependencies in requirements.txt. We utilized a modern backend web development stack of fastapi, uvicorn, httpx, and pydantic.

The fastapi is a a web framework used for building APIs with Python.

Uvicorn is a ASGI server needed to run the fastapi application

Httpx is a library for making HTTP requests.

Pydantic is a data validation library utilized by FastAPI to ensure data sent to and from the API is in correctly formatted.

### 2. Data Standardization

We needed to standardize schema being pulled from Genelab to ensure all incoming data follows a standardized format.

### Connector

genelab.py acts as a connector to fetch data on demand without storing files locally. This is especially important as the genomic data from genelab is quite extensive and can become quite large.

We use 'async def' allows the FastAPI to remain responsive and complete other tasks while it waits for the database to send data back.

Our 'async with' opesn the HTTP client safely and in the context of the 'async def' we make sure the loop isn't blocked while opening or closing network connections.

# Phase 2: AI Enginerring