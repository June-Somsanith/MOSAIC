# AI taggeer
# OSDR metadata has information we can use to tag genes with AI including: tissue type, experimental factors, organism, study type, etc.
# Useing Hugging Face transformers to build a simple tagging pipeline

from transformers import pipeline
import logging
from typing import List, Dict

# Logging configuration
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

# Zero-shot model for tagging
MODEL_NAME = "valhalla/distilbart-mnli-12-1"

class AITaggerServices:
    _classifier = None

    @classmethod
    def get_classifier(cls):
        if cls._classifier is None:
            logger.info(f"Loading AI mdoel: {MODEL_NAME}")
            try:
                cls._classifier = pipeline("zero-shot-classification", model = MODEL_NAME)
                logger.info("AI model loaded successfully.")
            except Exception as e:
                logger.error(f"Error loading AI model: {e}")
                raise e
        
        return cls._classifier
    
    @classmethod
    def tag_text(cls, text: str, candidate_labels: List[str] = None) -> Dict:
        # Standard Zero-shot classification on raw text

        if not text:
            return {"error": "No text provided for tagging."}
        
        if not candidate_labels:
            candidate_labels = [
                "Spaceflight",
                "Radiation",
                "Microgravity",
                "Oxidative Stress",
                "Immune Response",
                "Bone Density",
                "Muscle Atrophy",
                "Cardiovascular Health",
                "Gene Expression",
                "Cellular Stress",
                "Tissue Regeneration",
                "Plant Biology",
                "Microbial Response",
            ]

        classifier = cls.get_classifier()
        # This runs the AI model
        results = classifier(text, candidate_labels, multi_label = True)

        # Filter the results based on confidence
        filtered_results = {}
        for label, score in zip(results['labels'], results['scores']):
            if score >= .60:
                filtered_results[label] = round(score, 6)

        return {
            "tags": filtered_results,
            "top_tag": results['labels'][0]
        }
    
    @classmethod
    def generate_context_tags(cls, description: str, tissue: List[str], factors: List[str], organism: List[str]):
        # Combining Metadata and Description to give the AI more context for tagging
        rich_context = f"Tissue: {', '.join(tissue)}. Factors: {', '.join(factors)}. Organism: {', '.join(organism)}. {description}"

        return cls.tag_text(rich_context)