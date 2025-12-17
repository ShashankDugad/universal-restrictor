"""
Toxicity Detector - Hybrid approach: Keywords + Llama Guard 3.

Strategy:
1. Fast keyword check for obvious threats (high confidence)
2. Llama Guard for nuanced/borderline cases
3. Combined result for best accuracy
"""

import os
import re
import logging
from typing import List, Tuple

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

# Finance patterns to skip (handled by finance detector)
FINANCE_PATTERNS = [
    r'(?i)\b(buy|sell|target|nifty|sensex|reliance|tcs|hdfcbank|infy|stock|share|trading)\b',
    r'(?i)\b(loan|emi|interest|credit|account|bank|upi|ifsc)\b',
]

# High-confidence threat patterns (catches what Llama Guard misses)
THREAT_PATTERNS: List[Tuple[str, Category, Severity, str]] = [
    # Direct violence threats
    (r'(?i)\b(i\s+will\s+kill\s+you|i\'?m\s+going\s+to\s+kill\s+you|gonna\s+kill\s+you)', 
     Category.TOXIC_VIOLENCE, Severity.CRITICAL, "Direct death threat"),
    (r'(?i)\b(i\s+will\s+murder|i\'?m\s+going\s+to\s+murder|gonna\s+murder)', 
     Category.TOXIC_VIOLENCE, Severity.CRITICAL, "Murder threat"),
    (r'(?i)\b(kill\s+yourself|kys\b|go\s+die)', 
     Category.TOXIC_SELF_HARM, Severity.CRITICAL, "Encouraging self-harm"),
    (r'(?i)\b(i\s+will\s+shoot|i\'?m\s+going\s+to\s+shoot|gonna\s+shoot)\s+(you|him|her|them)', 
     Category.TOXIC_VIOLENCE, Severity.CRITICAL, "Shooting threat"),
    (r'(?i)\b(i\s+will\s+stab|i\'?m\s+going\s+to\s+stab|gonna\s+stab)', 
     Category.TOXIC_VIOLENCE, Severity.CRITICAL, "Stabbing threat"),
    (r'(?i)\b(i\s+will\s+hurt|i\'?m\s+going\s+to\s+hurt|gonna\s+hurt)\s+(you|him|her|them)', 
     Category.TOXIC_VIOLENCE, Severity.HIGH, "Threat of physical harm"),
    (r'(?i)\b(beat\s+you\s+up|kick\s+your\s+ass|smash\s+your\s+face)', 
     Category.TOXIC_VIOLENCE, Severity.HIGH, "Physical violence threat"),
    
    # Hate speech
    (r'(?i)\b(hate\s+all|eliminate\s+all|exterminate\s+all|kill\s+all)\s+\w+', 
     Category.TOXIC_HATE, Severity.CRITICAL, "Group hatred/genocide"),
    (r'(?i)\b(should\s+be\s+eliminated|should\s+all\s+die|deserve\s+to\s+die)', 
     Category.TOXIC_HATE, Severity.CRITICAL, "Dehumanizing speech"),
    (r'(?i)\b(subhuman|inferior\s+race|master\s+race)', 
     Category.TOXIC_HATE, Severity.CRITICAL, "Racial supremacy"),
    
    # Self-harm
    (r'(?i)\b(want\s+to\s+die|want\s+to\s+kill\s+myself|end\s+my\s+life)', 
     Category.TOXIC_SELF_HARM, Severity.CRITICAL, "Suicidal ideation"),
    (r'(?i)\b(how\s+to\s+commit\s+suicide|best\s+way\s+to\s+die|painless\s+death)', 
     Category.TOXIC_SELF_HARM, Severity.CRITICAL, "Seeking suicide methods"),
    
    # Weapons
    (r'(?i)\b(how\s+to\s+make\s+a?\s*bomb|build\s+a?\s*bomb|homemade\s+explosive)', 
     Category.TOXIC_VIOLENCE, Severity.CRITICAL, "Bomb-making"),
    (r'(?i)\b(how\s+to\s+make\s+poison|make\s+deadly\s+poison)', 
     Category.TOXIC_VIOLENCE, Severity.CRITICAL, "Poison-making"),
    
    # Sexual
    (r'(?i)\b(child\s+porn|cp\b|underage\s+sex|sex\s+with\s+minor)', 
     Category.TOXIC_SEXUAL, Severity.CRITICAL, "Child exploitation"),
]

_model_instance = None


def get_llm():
    global _model_instance
    
    if _model_instance is not None:
        return _model_instance
    
    # Try Q8 first (better), then Q4
    model_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", "models", "Llama-Guard-3-8B.Q8_0.gguf"),
        os.path.join(os.path.dirname(__file__), "..", "..", "models", "Llama-Guard-3-8B.Q4_K_M.gguf"),
    ]
    
    model_path = None
    for path in model_paths:
        if os.path.exists(path):
            model_path = path
            break
    
    if model_path is None:
        logger.warning("No Llama Guard model found")
        return None
    
    try:
        from llama_cpp import Llama
        
        logger.info(f"Loading Llama Guard 3 from {model_path}")
        _model_instance = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=-1,
            verbose=False,
            seed=42,
        )
        logger.info("Llama Guard 3 loaded")
        return _model_instance
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None


class ToxicityDetector:
    """
    Hybrid toxicity detection: Keywords + Llama Guard.
    """
    
    def __init__(self):
        self.name = "toxicity_hybrid"
        self._finance_patterns = [re.compile(p) for p in FINANCE_PATTERNS]
        self._threat_patterns = [
            (re.compile(pattern), category, severity, explanation)
            for pattern, category, severity, explanation in THREAT_PATTERNS
        ]
    
    def _is_finance_text(self, text: str) -> bool:
        """Check if text is finance-related."""
        for pattern in self._finance_patterns:
            if pattern.search(text):
                return True
        return False
    
    def _keyword_detect(self, text: str) -> List[Detection]:
        """Fast keyword-based detection for obvious threats."""
        detections = []
        
        for pattern, category, severity, explanation in self._threat_patterns:
            match = pattern.search(text)
            if match:
                detections.append(Detection(
                    category=category,
                    severity=severity,
                    confidence=0.98,  # High confidence for explicit patterns
                    matched_text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    explanation=explanation,
                    detector="toxicity_keyword"
                ))
        
        return detections
    
    def _llm_detect(self, text: str) -> List[Detection]:
        """LLM-based detection for nuanced cases."""
        llm = get_llm()
        
        if llm is None:
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
            output = llm(
                prompt, 
                max_tokens=50, 
                stop=['<|eot_id|>'],
                temperature=0.0,
            )
            result = output['choices'][0]['text'].strip()
            return self._parse_llm_result(result, text)
            
        except Exception as e:
            logger.error(f"LLM inference error: {e}")
            return []
    
    def _parse_llm_result(self, result: str, text: str) -> List[Detection]:
        """Parse Llama Guard output."""
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
                        confidence=0.90,  # Slightly lower confidence for LLM
                        matched_text=text[:100] + "..." if len(text) > 100 else text,
                        start_pos=0,
                        end_pos=len(text),
                        explanation=f"Unsafe content: {cat_name}",
                        detector="toxicity_llama_guard"
                    ))
        
        return detections
    
    def detect(self, text: str, threshold: float = 0.5) -> List[Detection]:
        """
        Detect toxic content using hybrid approach.
        
        1. Skip finance-related text
        2. Run keyword detection (fast, high precision)
        3. Run LLM detection (covers edge cases)
        4. Combine and deduplicate
        """
        # Skip finance text
        if self._is_finance_text(text):
            return []
        
        all_detections = []
        
        # Fast keyword detection first
        keyword_detections = self._keyword_detect(text)
        all_detections.extend(keyword_detections)
        
        # If keywords found critical threats, no need for LLM
        has_critical = any(d.severity == Severity.CRITICAL for d in keyword_detections)
        
        if not has_critical:
            # Run LLM for nuanced detection
            llm_detections = self._llm_detect(text)
            all_detections.extend(llm_detections)
        
        # Deduplicate by category
        seen_categories = set()
        unique_detections = []
        for d in sorted(all_detections, key=lambda x: x.confidence, reverse=True):
            if d.category not in seen_categories:
                seen_categories.add(d.category)
                unique_detections.append(d)
        
        return unique_detections
