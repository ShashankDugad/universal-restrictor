"""
Toxicity Detector - ML-based detection for harmful content.

Uses a lightweight transformer model that runs on CPU.
Model: unitary/toxic-bert or similar distilled model

Categories detected:
- Hate speech
- Harassment
- Violence
- Sexual content
- Self-harm
- Profanity
"""

from typing import List, Optional, Dict
import logging

from ..models import Detection, Category, Severity

logger = logging.getLogger(__name__)


# Mapping from model labels to our categories
TOXICITY_LABEL_MAP = {
    "toxic": Category.TOXIC_PROFANITY,
    "severe_toxic": Category.TOXIC_HATE,
    "obscene": Category.TOXIC_PROFANITY,
    "threat": Category.TOXIC_VIOLENCE,
    "insult": Category.TOXIC_HARASSMENT,
    "identity_hate": Category.TOXIC_HATE,
    "identity_attack": Category.TOXIC_HATE,
    "sexual_explicit": Category.TOXIC_SEXUAL,
    "hate": Category.TOXIC_HATE,
    "harassment": Category.TOXIC_HARASSMENT,
    "violence": Category.TOXIC_VIOLENCE,
    "self-harm": Category.TOXIC_SELF_HARM,
    "sexual": Category.TOXIC_SEXUAL,
    "profanity": Category.TOXIC_PROFANITY,
}

# Severity mapping based on category
CATEGORY_SEVERITY = {
    Category.TOXIC_HATE: Severity.CRITICAL,
    Category.TOXIC_HARASSMENT: Severity.HIGH,
    Category.TOXIC_VIOLENCE: Severity.CRITICAL,
    Category.TOXIC_SEXUAL: Severity.HIGH,
    Category.TOXIC_SELF_HARM: Severity.CRITICAL,
    Category.TOXIC_PROFANITY: Severity.MEDIUM,
}


class ToxicityDetector:
    """
    Detect toxic content using a transformer model.
    
    Lazy loads model on first use to keep startup fast.
    Falls back to keyword matching if model unavailable.
    """
    
    def __init__(self, model_name: str = "unitary/toxic-bert", use_gpu: bool = False):
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.name = "toxicity_ml"
        
        self._classifier = None
        self._model_loaded = False
        self._fallback_mode = False
        
        # Fallback keywords for when model isn't available
        self._toxic_keywords = self._build_keyword_list()
    
    def _build_keyword_list(self) -> Dict[Category, List[str]]:
        """Build fallback keyword lists for each category."""
        return {
            Category.TOXIC_PROFANITY: [
                "fuck", "shit", "damn", "ass", "bitch", "crap",
                "bastard", "dick", "piss", "cunt",
            ],
            Category.TOXIC_HATE: [
                "nazi", "nigger", "faggot", "kike", "spic", "chink",
                "retard", "terrorist",
            ],
            Category.TOXIC_VIOLENCE: [
                "kill you", "murder", "shoot you", "stab you", 
                "beat you up", "death threat", "bomb", "attack",
            ],
            Category.TOXIC_HARASSMENT: [
                "loser", "idiot", "moron", "stupid", "dumb",
                "pathetic", "worthless", "ugly",
            ],
        }
    
    def _load_model(self):
        """Lazy load the toxicity model."""
        if self._model_loaded:
            return
        
        try:
            from transformers import pipeline
            
            device = 0 if self.use_gpu else -1
            
            self._classifier = pipeline(
                "text-classification",
                model=self.model_name,
                top_k=None,  # Return all labels
                device=device,
                truncation=True,
                max_length=512
            )
            self._model_loaded = True
            logger.info(f"Loaded toxicity model: {self.model_name}")
            
        except ImportError:
            logger.warning("transformers not installed. Using keyword fallback.")
            self._fallback_mode = True
            self._model_loaded = True
            
        except Exception as e:
            logger.warning(f"Failed to load model: {e}. Using keyword fallback.")
            self._fallback_mode = True
            self._model_loaded = True
    
    def detect(self, text: str, threshold: float = 0.5) -> List[Detection]:
        """
        Detect toxic content in text.
        
        Args:
            text: Input text to analyze
            threshold: Minimum confidence to report (0.0-1.0)
            
        Returns:
            List of Detection objects for toxic content found
        """
        self._load_model()
        
        if self._fallback_mode:
            return self._detect_keywords(text, threshold)
        
        return self._detect_ml(text, threshold)
    
    def _detect_ml(self, text: str, threshold: float) -> List[Detection]:
        """Detect using ML model."""
        detections = []
        
        try:
            # Run classifier
            results = self._classifier(text)
            
            # Results is a list of dicts: [{"label": ..., "score": ...}, ...]
            if results and isinstance(results[0], list):
                results = results[0]  # Handle nested list from top_k
            
            for result in results:
                label = result["label"].lower()
                score = result["score"]
                
                if score < threshold:
                    continue
                
                # Map to our category
                category = TOXICITY_LABEL_MAP.get(label)
                if not category:
                    # Try partial match
                    for key, cat in TOXICITY_LABEL_MAP.items():
                        if key in label or label in key:
                            category = cat
                            break
                
                if not category:
                    category = Category.TOXIC_PROFANITY  # Default
                
                severity = CATEGORY_SEVERITY.get(category, Severity.MEDIUM)
                
                # Adjust severity based on confidence
                if score > 0.9:
                    if severity == Severity.MEDIUM:
                        severity = Severity.HIGH
                    elif severity == Severity.HIGH:
                        severity = Severity.CRITICAL
                
                detections.append(Detection(
                    category=category,
                    severity=severity,
                    confidence=score,
                    matched_text=text[:100] + "..." if len(text) > 100 else text,
                    start_pos=0,
                    end_pos=len(text),
                    explanation=f"Toxic content detected: {label} (confidence: {score:.2f})",
                    detector=self.name
                ))
        
        except Exception as e:
            logger.error(f"ML detection failed: {e}")
            return self._detect_keywords(text, threshold)
        
        return detections
    
    def _detect_keywords(self, text: str, threshold: float) -> List[Detection]:
        """Fallback keyword-based detection."""
        detections = []
        text_lower = text.lower()
        
        for category, keywords in self._toxic_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Find position
                    start = text_lower.find(keyword)
                    end = start + len(keyword)
                    
                    severity = CATEGORY_SEVERITY.get(category, Severity.MEDIUM)
                    
                    detections.append(Detection(
                        category=category,
                        severity=severity,
                        confidence=0.70,  # Lower confidence for keyword match
                        matched_text=text[start:end],
                        start_pos=start,
                        end_pos=end,
                        explanation=f"Toxic keyword detected: '{keyword}'",
                        detector="toxicity_keyword_fallback"
                    ))
        
        # Deduplicate - keep highest severity per category
        seen_categories = {}
        for d in detections:
            if d.category not in seen_categories:
                seen_categories[d.category] = d
            elif list(Severity).index(d.severity) > list(Severity).index(seen_categories[d.category].severity):
                seen_categories[d.category] = d
        
        return list(seen_categories.values())
