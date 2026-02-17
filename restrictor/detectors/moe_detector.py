"""
2-Stage MoE Detector using MuRIL.

Stage 1: Binary (toxic/safe) - High recall
Stage 2: Category classifier - For toxic content
"""
import os
import logging
from typing import List, Optional, Tuple
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

from restrictor.models import Detection, Category, Severity

logger = logging.getLogger(__name__)


class MoEDetector:
    """2-Stage Mixture of Experts detector."""
    
    # Category to internal category mapping
    CATEGORY_MAP = {
        "harassment": Category.TOXIC_HARASSMENT,
        "harmful_content": Category.TOXIC_VIOLENCE,
        "hate_speech": Category.TOXIC_HATE,
        "hindi_abuse": Category.TOXIC_HARASSMENT,
        "self_harm": Category.TOXIC_SELF_HARM,
        "sexual": Category.TOXIC_SEXUAL,
    }
    
    # Category to severity mapping
    SEVERITY_MAP = {
        "harassment": Severity.HIGH,
        "harmful_content": Severity.CRITICAL,
        "hate_speech": Severity.CRITICAL,
        "hindi_abuse": Severity.HIGH,
        "self_harm": Severity.CRITICAL,
        "sexual": Severity.HIGH,
    }
    
    def __init__(
        self,
        stage1_path: str = "models/moe_muril/stage1_binary",
        stage2_path: str = "models/moe_muril/stage2_category",
        device: Optional[str] = None,
        confidence_threshold: float = 0.5,
    ):
        self.stage1_path = stage1_path
        self.stage2_path = stage2_path
        self.confidence_threshold = confidence_threshold
        self.stage1 = None
        self.stage2 = None
        self._loaded = False
        
        # Determine device
        if device:
            self.device = device
        elif torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"
    
    def load(self) -> bool:
        """Load both stages of the MoE model."""
        if self._loaded:
            return True
        
        try:
            logger.info(f"Loading MoE Stage 1 from {self.stage1_path}...")
            self.stage1 = pipeline(
                "text-classification",
                model=self.stage1_path,
                tokenizer=self.stage1_path,
                device=self.device if self.device != "mps" else -1,
                truncation=True,
                max_length=256,
            )
            
            logger.info(f"Loading MoE Stage 2 from {self.stage2_path}...")
            self.stage2 = pipeline(
                "text-classification",
                model=self.stage2_path,
                tokenizer=self.stage2_path,
                device=self.device if self.device != "mps" else -1,
                truncation=True,
                max_length=256,
            )
            
            self._loaded = True
            logger.info(f"MoE detector loaded successfully (device: {self.device})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load MoE detector: {e}")
            return False
    
    def detect(self, text: str) -> List[Detection]:
        """
        Run 2-stage detection.
        
        Stage 1: Is it toxic?
        Stage 2: What category?
        """
        if not self._loaded:
            if not self.load():
                return []
        
        detections = []
        
        try:
            # Stage 1: Binary classification
            stage1_result = self.stage1(text)[0]
            stage1_label = stage1_result["label"]
            stage1_conf = stage1_result["score"]
            
            # If safe, return empty
            if stage1_label == "safe" and stage1_conf > self.confidence_threshold:
                return []
            
            # Stage 2: Category classification
            stage2_result = self.stage2(text)[0]
            category_label = stage2_result["label"]
            stage2_conf = stage2_result["score"]
            
            # Combined confidence
            combined_conf = stage1_conf * stage2_conf
            
            # Map to internal category
            category = self.CATEGORY_MAP.get(category_label, Category.TOXIC_HARASSMENT)
            severity = self.SEVERITY_MAP.get(category_label, Severity.HIGH)
            
            detection = Detection(
                category=category,
                confidence=round(combined_conf, 4),
                severity=severity,
                detector=f"moe_{category_label}",
                explanation=f"MoE detected {category_label} content",
                start_pos=0,
                end_pos=len(text),
                matched_text=text[:100],
            )
            detections.append(detection)
            
        except Exception as e:
            logger.error(f"MoE detection error: {e}")
        
        return detections
    
    def classify(self, text: str) -> dict:
        """
        Get full classification result.
        
        Returns:
            dict with is_toxic, category, confidence, stage1_conf, stage2_conf
        """
        if not self._loaded:
            if not self.load():
                return {"is_toxic": False, "category": "safe", "confidence": 0.0}
        
        try:
            # Stage 1
            r1 = self.stage1(text)[0]
            
            if r1["label"] == "safe":
                return {
                    "is_toxic": False,
                    "category": "safe",
                    "confidence": r1["score"],
                    "stage1_conf": r1["score"],
                    "stage2_conf": None,
                }
            
            # Stage 2
            r2 = self.stage2(text)[0]
            
            return {
                "is_toxic": True,
                "category": r2["label"],
                "confidence": r1["score"] * r2["score"],
                "stage1_conf": r1["score"],
                "stage2_conf": r2["score"],
            }
            
        except Exception as e:
            logger.error(f"MoE classify error: {e}")
            return {"is_toxic": False, "category": "error", "confidence": 0.0}


# Singleton instance
_moe_detector: Optional[MoEDetector] = None


def get_moe_detector() -> MoEDetector:
    """Get or create the MoE detector singleton."""
    global _moe_detector
    if _moe_detector is None:
        _moe_detector = MoEDetector()
    return _moe_detector
