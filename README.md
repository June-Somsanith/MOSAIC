# MOSAIC: Multi-Organism Spaceflight Analysis and Integrated Comparison
This project is currently under construction.

## Purpose
The purpose of this project is to gather information on the orthologous gene dysregulation from species to species or kingdom to kingdom that occurs during spaceflight. Spaceflight research is often limited by high costs, intensive resource requirements, and difficulties in replicating studies. To accelerate future discoveries, it is crucial to consolidate existing data. This model will facilitate the comparison of dysregulated orthologous genes from various spaceflight experiments, offering insights into the biological responses to spaceflight.

## Important Considerations
While the MOSAIC model enables the simultaneous comparison of multiple studies involving similar or different species, we recommend analyzing **no more than five studies at a time** to maintain data integrity. It is important to acknowledge that due to the inherent limitations of spaceflight research, such as small sample sizes and limited replicatations, data sets may be disparate. For example, a study with five subjects of one species may be compared to another with 25 subjects of a different species, which could potentially skew the results.

## Beyond Spaceflight
While MOSAIC was conceived to address challenges in spaceflight research, its application is not confined to this field. The framework is adaptable for any orthologous gene comparison across a wide range of biological studies, provided the necessary data is available. The potential comparisons and subsequent discoveries are limited only by the scope of the user's inquiry and the current available data.

# Methods

## 1. Creating the orthologous analysis code

## 2. Cleaning up data/code

Originally we had a collection of different manual scripts. We needed to combine and condense these scripts to run automatically and streamline the logic into a servicable application.

We created the `orthology.py` file to stand in place of our `BiomaRt` and `Species_orthology_link` scripts. This new script is able to handle gene ID mapping.

The `analytics.py` combined our `Merging_dataframes.txt` and `AWG_transcriptomics_sorting_&adapted_IDEP9.3_code.R` into a comprehensive script that could handle the merging of datasets along with normalization and PCA in one.

The `schemas.py` defines the Pydantic models and acts as a filter. This layer ensure data coming from NASA or going to the AI is formatted correctly.

The `main.py` utilizes FASTAPI and Uvicorn to coordinat the other scripts.

## 3. Phase 1: Core Data Infrastructure

### 1. Installing dependencies

We first listed our dependencies in requirements.txt. We utilized a modern backend web development stack of FASTAPI, Uvicorn, Httpx, and Pydantic.

The FASTAPI is a a web framework used for building APIs with Python.

Uvicorn is a ASGI server needed to run the FASTAPI application

Httpx is a library for making HTTP requests.

Pydantic is a data validation library utilized by FastAPI to ensure data sent to and from the API is in correctly formatted.

### 2. Data Standardization

We needed to standardize schema being pulled from Genelab to ensure all incoming data follows a standardized format.

### Connector

genelab.py acts as a connector to fetch data on demand without storing files locally. This is especially important as the genomic data from genelab is quite extensive and can become quite large.

We use `async def` allows the FastAPI to remain responsive and complete other tasks while it waits for the database to send data back.

Our `async with` opesn the HTTP client safely and in the context of the 'async def' we make sure the loop isn't blocked while opening or closing network connections.

## Phase 2: AI Engineering

Phase 1 handles the quantitative data while phase 2 will handle the qualtitative data. Genelab study's metatdata can be difficult to categorize via title and study description without manual review. Our goal is to implement a Natural Language Processing (NLP) pipeline to classify text into categoriacl labels or taggs.

### 1. NLP Pipeline and Automated Tagging Service
We created a `ai_tagger.py` within the FastAPI backend. This service:
1. Recieves the raw text data description from NASA OSDR metadata
2. Passes it through the transformer model
3. Returns a ranked list of relevant scientific tags to the frontend

This will allow our application to move from a data viewer to an ai research assistant that helps scientists discover relevant studies.

We utilized a Zero-shot method, which is a machine learning method in which the AI model is trained to recognize objects and concepts and catrogrize them without necessarily having seen an example of the object beforehand. The Zero-shot method allows us to make the application scalalbe as supervised learning, as is common in deep learning models, is time consuming. The annotation of large amounts of data samples is impractical.

We chose the model `valhalla/distilbart-mnli-12-1` as it's speeds were the fasts of the three most common models and is more friendly towards local testing and execution. The "facebook/bart-large-mnli" model was the second contender as it's generally the "Gold Standard" and has a high intelligence, however the speeds are slow in comparison to the valhalla and uses 2x more RAM. Due to these factors, we chose to go with the valhalla model.

We updated the script for:
* Hardware acceleration through `torch.cuda` to detect and utilize GPU
* Token management to keep the model within a ~512-token limit
* Batch inference for simultaneouse tagging of studies

We conducted hypothesis tuning with `test_script.py` to calibrate the AI to interpret text. Our script attempt to yield the highest confidence and best separtion between catoagories within the OSDR studies.

The first version of this test resulted in a 0.96 confidence score, which indicates when the current model is searching for a stressor, it identifies it with near-certainy.

# Results

We tested our application using industry standards for python: pytest. We did this by creating a test suite and a script that runs on fastapi.testclient to test if our endpoints are behaving correctly.
