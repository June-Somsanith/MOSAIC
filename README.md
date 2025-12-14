# MOSAIC: Multi-Organism Spaceflight Analysis and Integrated Comparison
This project is currently under construction.

## Purpose
The purpose of this project is to gather information on the orthologis gene disregulation from species to species or kingdom to kingdom that occurs during spaceflight. Spaceflight research is often limited by high costs, intensive resource requirements, and difficulties in replicating studies. To accelerate future discoveries, it is crucial to consolidate existing data. This model will facilitate the comparison of dysregulated orthologous genes from various spaceflight experiments, offering insights into the biological responses to spaceflight.

## Important Considerations
While this model enables the simultaneous comparison of multiple studies involving similar or different species, we recommend analyzing no more than five studies at a time to maintain data integrity. It is important to acknowledge that due to the inherent limitations of spaceflight research, such as small sample sizes and limited replicatations, data sets may be disparate. For example, a study with five subjects of one species may be compared to another with 25 subjects of a different species, which could potentially skew the results.

## Beyond Spaceflight
While MOSAIC was conceived to address challenges in spaceflight research, its application is not confined to this field. The framework is adaptable for any orthologous gene comparison across a wide range of biological studies, provided the necessary data is available. The potential comparisons and subsequent discoveries are limited only by the scope of the user's inquiry and the current available data.

# Methods

## 1. Creating the orthologous analysis code

## 2. Cleaning up data/code

Originally we had a collection of different manual scripts. We needed to combine and condense these scripts to run automatically and streamline the logic into a servicable application.

We created the orthology.py file to stand in place of our BiomaRt and Species_orthology_link scripts. This new script is able to handle gene ID mapping.

The analytics.py combined our Merging_dataframes.txt and AWG_transcriptomics_sorting_&adapted_IDEP9.3_code.R into a comprehensive script that could handle the merging of datasets along with normalization and PCA in one.

## 3. Phase 1: Create the application

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

## Phase 2: AI Enginerring