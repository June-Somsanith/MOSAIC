# AI taggeer
# OSDR metadata has information we can use to tag genes with AI including: tissue type, experimental factors, organism, study type, etc.
# Useing Hugging Face transformers to build a simple tagging pipeline

from transformers import pipeline
import torch
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
            # 1. Determine if GPU is available
            device = 0 if torch.cuda.is_available() else -1
            device_name = "GPU" if device == 0 else "CPU"

            logger.info(f"Loading AI model: {MODEL_NAME} on {device_name}")
            
            try:
                cls._classifier = pipeline(
                    "zero-shot-classification",
                    model = MODEL_NAME,
                    device = device,
                    model_kwargs = {"truncation": True}
                    )
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
        hypothesis_template = "This study relates to {}."

        # This runs the AI model
        results = classifier(
            text,
            candidate_labels,
            multi_label = True,
            hypothesis_template = hypothesis_template
            )

        # Filter the results based on confidence
        filtered_results = {}
        for label, score in zip(results['labels'], results['scores']):
            if score >= .60:
                filtered_results[label] = round(score, 6)

        return {
            "tags": filtered_results,
            "top_tag": results['labels'][0] if results['labels'] else None
        }
    
    @classmethod
    def generate_context_tags(cls, description: str, tissue: List[str], factors: List[str], organism: List[str]):
        # Combining Metadata and Description to give the AI more context for tagging
        rich_context = f"Tissue: {', '.join(tissue)}. Factors: {', '.join(factors)}. Organism: {', '.join(organism)}. {description}"

        safe_context = cls.truncate_context(rich_context)
        return cls.tag_text(safe_context)
    
    @staticmethod
    def truncate_context(text: str, max_chars: int = 1800) -> str:
        # Truncates text to fit within a ~512 token limit
        # If text is too long, we keep the beginning and end
        
        if len(text) <= max_chars:
            return text
        
        # Keep first 1200 chars and last 500 chars
        half_buffer = max_chars // 2
        return f"{text[:1200]} ... [truncated] ... {text[-500:]}"