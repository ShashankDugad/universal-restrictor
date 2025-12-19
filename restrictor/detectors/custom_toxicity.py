"""
Custom toxicity detector using your fine-tuned model.
This is YOUR IP - trained on your data.
"""
import os
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Model path
MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../models/restrictor-model-final")

# Global model instance
_classifier = None
_model_loaded = False


def get_classifier():
    """Load model once, reuse."""
    global _classifier, _model_loaded
    
    if _model_loaded:
        return _classifier
    
    if not os.path.exists(MODEL_PATH):
        logger.warning(f"Custom model not found at {MODEL_PATH}")
        _model_loaded = True
        return None
    
    try:
        from transformers import pipeline
        logger.info(f"Loading custom toxicity model from {MODEL_PATH}")
        _classifier = pipeline(
            "text-classification",
            model=MODEL_PATH,
            device=-1  # CPU, change to 0 for GPU
        )
        logger.info("Custom toxicity model loaded successfully")
        _model_loaded = True
        return _classifier
    except Exception as e:
        logger.error(f"Failed to load custom model: {e}")
        _model_loaded = True
        return None


def detect_toxicity(text: str, threshold: float = 0.7) -> Tuple[bool, float, str]:
    """
    Detect toxicity using custom trained model.
    
    Returns:
        (is_toxic, confidence, label)
    """
    classifier = get_classifier()
    
    if classifier is None:
        return False, 0.0, "model_not_loaded"
    
    try:
        result = classifier(text[:512])[0]  # Truncate to max length
        label = result["label"]
        score = result["score"]
        
        is_toxic = label == "toxic" and score >= threshold
        
        return is_toxic, score, label
        
    except Exception as e:
        logger.error(f"Toxicity detection error: {e}")
        return False, 0.0, "error"


def detect(text: str, threshold: float = 0.7) -> dict:
    """
    Main detection function.
    
    Returns:
        {
            "is_toxic": bool,
            "confidence": float,
            "label": str,
            "model": "custom-v1"
        }
    """
    is_toxic, confidence, label = detect_toxicity(text, threshold)
    
    return {
        "is_toxic": is_toxic,
        "confidence": confidence,
        "label": label,
        "model": "custom-v1"
    }


# Test function
if __name__ == "__main__":
    test_texts = [
        "Hello, how are you?",
        "I will kill you",
        "The weather is nice today",
        "You are worthless garbage",
        "तू मर जा साले",
        "आज मौसम अच्छा है",
    ]
    
    print("Testing custom toxicity model...")
    print("=" * 60)
    
    for text in test_texts:
        result = detect(text)
        status = "🚫 TOXIC" if result["is_toxic"] else "✅ SAFE"
        print(f"{status} ({result['confidence']:.3f}) | {text[:40]}")
