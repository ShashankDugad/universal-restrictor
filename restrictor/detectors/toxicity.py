"""
Toxicity Detector - Local Llama Guard 3 (no external API).
"""

import os
import re
import logging
from typing import List

from ..models import Detection, Category, Severity

logger = logging.getLogger(__name__)

LLAMA_GUARD_CATEGORIES = {
    "S1": ("violent_crimes", Category.TOXIC_VIOLENCE, Severity.CRITICAL),
    "S2": ("non_violent_crimes", Category.TOXIC_HARASSMENT, Severity.HIGH),
    "S3": ("sex_related_crimes", Category.TOXIC_SEXUAL, Severity.CRITICAL),
    "S4": ("hate", Category.TOXIC_HATE, Severity.CRITICAL),
    "S5": ("defamation", Category.TOXIC_HARASSMENT, Severity.MEDIUM),
    "S6": ("specialized_advice", Category.TOXIC_HARASSMENT, Severity.LOW),
    "S7": ("privacy", Category.TOXIC_HARASSMENT, Severity.MEDIUM),
    "S8": ("intellectual_property", Category.TOXIC_HARASSMENT, Severity.LOW),
    "S9": ("indiscriminate_weapons", Category.TOXIC_VIOLENCE, Severity.CRITICAL),
    "S10": ("hate", Category.TOXIC_HATE, Severity.CRITICAL),
    "S11": ("suicide_self_harm", Category.TOXIC_SELF_HARM, Severity.CRITICAL),
    "S12": ("sexual_content", Category.TOXIC_SEXUAL, Severity.HIGH),
    "S13": ("elections", Category.TOXIC_HARASSMENT, Severity.MEDIUM),
}

# Finance-related patterns (to filter false positives)
FINANCE_PATTERNS = [
    r'(?i)\b(buy|sell|target|nifty|sensex|reliance|tcs|hdfcbank|infy|stock|share|trading)\b',
    r'(?i)\b(loan|emi|interest|credit|account|bank|upi|ifsc)\b',
]

_model_instance = None


def get_llm():
    global _model_instance
    
    if _model_instance is not None:
        return _model_instance
    
    model_path = os.path.join(
        os.path.dirname(__file__),
        "..", "..", "models", "Llama-Guard-3-8B.Q4_K_M.gguf"
    )
    
    if not os.path.exists(model_path):
        logger.warning(f"Model not found: {model_path}")
        return None
    
    try:
        from llama_cpp import Llama
        
        logger.info("Loading Llama Guard 3...")
        _model_instance = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=-1,
            verbose=False
        )
        logger.info("Llama Guard 3 loaded")
        return _model_instance
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None


class ToxicityDetector:
    def __init__(self):
        self.name = "toxicity_llama_guard_local"
        self._finance_patterns = [re.compile(p) for p in FINANCE_PATTERNS]
    
    def _is_finance_text(self, text: str) -> bool:
        """Check if text is finance-related."""
        for pattern in self._finance_patterns:
            if pattern.search(text):
                return True
        return False
    
    def detect(self, text: str, threshold: float = 0.5) -> List[Detection]:
        llm = get_llm()
        
        if llm is None:
            return self._fallback_detect(text)
        
        # Skip toxicity check for finance-related text (handled by finance detector)
        if self._is_finance_text(text):
            return []
        
        prompt = f'''<|begin_of_text|><|start_header_id|>user<|end_header_id|>

Task: Check if there is unsafe content in 'User' messages in conversations according to our safety policy.

<BEGIN CONVERSATION>

User: {text}

<END CONVERSATION>

Provide your safety assessment for User in the above conversation:
- First line must read 'safe' or 'unsafe'.
- If unsafe, a second line must include a comma-separated list of violated categories.<|eot_id|><|start_header_id|>assistant<|end_header_id|>

'''
        
        try:
            output = llm(prompt, max_tokens=50, stop=['<|eot_id|>'])
            result = output['choices'][0]['text'].strip()
            return self._parse_result(result, text)
            
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return self._fallback_detect(text)
    
    def _parse_result(self, result: str, text: str) -> List[Detection]:
        detections = []
        lines = result.strip().split('\n')
        
        if not lines or lines[0].lower().startswith('safe'):
            return []
        
        if lines[0].lower().startswith('unsafe'):
            categories = []
            for line in lines:
                for word in line.replace(',', ' ').split():
                    word = word.strip().upper()
                    if word.startswith('S') and len(word) <= 3 and word[1:].isdigit():
                        categories.append(word)
            
            if not categories:
                categories = ['S10']
            
            for cat in categories:
                if cat in LLAMA_GUARD_CATEGORIES:
                    cat_name, our_category, severity = LLAMA_GUARD_CATEGORIES[cat]
                    
                    detections.append(Detection(
                        category=our_category,
                        severity=severity,
                        confidence=0.95,
                        matched_text=text[:100] + "..." if len(text) > 100 else text,
                        start_pos=0,
                        end_pos=len(text),
                        explanation=f"Unsafe content: {cat_name}",
                        detector=self.name
                    ))
        
        return detections
    
    def _fallback_detect(self, text: str) -> List[Detection]:
        detections = []
        text_lower = text.lower()
        
        toxic_keywords = {
            Category.TOXIC_HATE: ['hate all', 'eliminate them', 'exterminate'],
            Category.TOXIC_VIOLENCE: ['kill you', 'murder you', 'shoot you', 'stab you'],
            Category.TOXIC_SELF_HARM: ['kill myself', 'suicide', 'end my life'],
        }
        
        for category, keywords in toxic_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    detections.append(Detection(
                        category=category,
                        severity=Severity.HIGH,
                        confidence=0.7,
                        matched_text=kw,
                        start_pos=text_lower.find(kw),
                        end_pos=text_lower.find(kw) + len(kw),
                        explanation=f"Toxic keyword: {kw}",
                        detector="toxicity_fallback"
                    ))
                    break
        
        return detections
