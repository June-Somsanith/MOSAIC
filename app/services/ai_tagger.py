# AI taggeer
# OSDR metadata has information we can use to tag genes with AI including: tissue type, experimental factors, organism, study type, etc.
# Useing Hugging Face transformers to build a simple tagging pipeline

from transformers import pipeline
import torch
import logging
import os
from typing import List, Dict, Union, Optional

# Logging configuration
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

# Zero-shot model for tagging
MODEL_NAME = "valhalla/distilbart-mnli-12-1"

# Adding default biological and environmental labels for OSDR context
# Consolidating Labels to prevent probabliity splitting
DEFAULT_LABELS = [
    "Spaceflight Environment",
    "Ground Control",
    "Metabolic Dysregulation",
    "Radiation Stress",
    "Immune Dysfunction",
    "Musculoskeletal Atrophy",
    "DNA Damage & Repair",
    "Oxidative Stress",
    "Tissue Regeneration",
    "Transcriptional Profiling",
]

class AITaggerServices:
    _classifier = None

    @classmethod
    def get_classifier(cls):
        """
        Initializes and returns the zero-shot classification pipeline. Caches the model for future use.
        """
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
    def tag_text(cls, input_data: Union[str, List[str]], candidate_labels: Optional[List[str]] = None) -> Union[Dict, List[Dict]]:
        """
        Exectures zero-shot classification using the high-performance 'stressor' template
         - Accepts single string or list of strings for batch processing
         - Returns tags with confidence scores, primary stressor, and high-confidence alerts
        """

        if not input_data:
            return {"error": "No text provided for tagging."}
        
        labels = candidate_labels if candidate_labels else DEFAULT_LABELS

        classifier = cls.get_classifier()
        hypothesis_template = "The primary biological stressor in this spaceflight study is {}."

        is_single = isinstance(input_data, str)
        batch = [input_data] if is_single else input_data

        logger.info(f"INFERENCE: Executing biologioal classification rep for {len(batch)} inputs...")

        # Execute Batch Inference
        # Pipeline can handle both single string and list of strings
        
        batch_results = classifier(
            batch,
            labels,
            multi_label = True,
            hypothesis_template = hypothesis_template,
            batch_size = 8 # Adjust batch size as needed to optimize performance
        )

        # Process results to filter by confidence
        processed_output = []
        for res in batch_results:
            filtered_tags = {
                label: round(score, 4)
                for label, score in zip(res['labels'], res['scores'])
                if score >= 0.05
            }

            processed_output.append({
                "tags": filtered_tags,
                "primary_stressor": res['labels'][0] if res['labels'] else None,
                "confidence": round(res['scores'][0], 4) if res['scores'] else 0,
                "high_confidence_alert": res['scores'][0] >=0.95
            })

        return processed_output[0] if is_single else processed_output

    @classmethod
    def generate_context_tags(cls, description: str, tissue: List[str], factors: List[str], organism: List[str]):
        # Combining Metadata and Description to give the AI more context for tagging
        t_str = ', '.join(tissue) if tissue else "Unknown"
        f_str = ', '.join(factors) if factors else "Unknown"
        o_str = ', '.join(organism) if organism else "Unknown"

        # Constructing the high-intensity stimulus string
        base_context = f"SUBJECT: {o_str} | TISSUE: {t_str} | STRESSORS: {f_str} | DESCRIPTION: {description}"
        rich_context = f"{base_context} | SUMMARY: Biological investigation of {t_str} in {o_str} involving {f_str}."
        
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