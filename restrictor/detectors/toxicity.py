"""
Toxicity Detector - Using Llama Guard 3 via Groq API.

Llama Guard 3 is Meta's safety classifier trained to detect:
- Violent Crimes
- Non-Violent Crimes
- Sex-Related Crimes
- Child Sexual Exploitation
- Defamation
- Specialized Advice
- Privacy
- Intellectual Property
- Indiscriminate Weapons
- Hate
- Suicide & Self-Harm
- Sexual Content
- Elections

Falls back to keyword matching if API unavailable.
"""

import os
import logging
from typing import List, Optional, Dict

from ..models import Detection, Category, Severity

logger = logging.getLogger(__name__)

# Llama Guard 3 categories mapped to our categories
LLAMA_GUARD_CATEGORY_MAP = {
    "S1": ("violent_crimes", Category.TOXIC_VIOLENCE, Severity.CRITICAL),
    "S2": ("non_violent_crimes", Category.TOXIC_HARASSMENT, Severity.HIGH),
    "S3": ("sex_related_crimes", Category.TOXIC_SEXUAL, Severity.CRITICAL),
    "S4": ("child_exploitation", Category.TOXIC_SEXUAL, Severity.CRITICAL),
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

CATEGORY_EXPLANATIONS = {
    "S1": "Violent crimes content detected",
    "S2": "Non-violent crimes content detected",
    "S3": "Sex-related crimes content detected",
    "S4": "Child exploitation content detected",
    "S5": "Defamatory content detected",
    "S6": "Specialized advice (medical/legal/financial) detected",
    "S7": "Privacy violation content detected",
    "S8": "Intellectual property violation detected",
    "S9": "Weapons/explosives content detected",
    "S10": "Hate speech detected",
    "S11": "Suicide or self-harm content detected",
    "S12": "Sexual content detected",
    "S13": "Election misinformation detected",
}


class ToxicityDetector:
    """
    Detect toxic content using Llama Guard 3 via Groq API.
    
    Llama Guard 3 is Meta's state-of-the-art safety classifier.
    Uses Groq for fast, free inference.
    
    Falls back to keyword matching if API unavailable.
    """
    
    def __init__(self, use_gpu: bool = False):
        """
        Initialize the detector.
        
        Args:
            use_gpu: Ignored (using API), kept for interface compatibility
        """
        self.name = "toxicity_llama_guard_3"
        self.model_name = "meta-llama/llama-guard-4-12b"
        
        self._client = None
        self._api_available = False
        self._initialized = False
        
        # Fallback keywords
        self._toxic_keywords = self._build_keyword_list()
    
    def _build_keyword_list(self) -> Dict[Category, List[str]]:
        """Build fallback keyword lists for each category."""
        return {
            Category.TOXIC_PROFANITY: [
                "fuck", "shit", "damn", "bitch", "crap",
                "bastard", "dick", "piss", "cunt", "asshole",
            ],
            Category.TOXIC_HATE: [
                "nazi", "faggot", "retard",
            ],
            Category.TOXIC_VIOLENCE: [
                "kill you", "murder you", "shoot you", "stab you",
                "beat you up", "death threat", "i will kill",
                "going to kill", "want to kill",
            ],
            Category.TOXIC_HARASSMENT: [
                "loser", "idiot", "moron", "stupid",
                "pathetic", "worthless", "ugly", "disgusting",
            ],
            Category.TOXIC_SELF_HARM: [
                "kill myself", "want to die", "end my life",
                "suicide", "cut myself",
            ],
        }
    
    def _init_client(self):
        """Initialize Groq client."""
        if self._initialized:
            return
        
        try:
            # Load environment variables
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.getenv("GROQ_API_KEY")
            
            if not api_key:
                logger.warning("GROQ_API_KEY not found in environment. Using keyword fallback.")
                self._api_available = False
                self._initialized = True
                return
            
            from groq import Groq
            
            self._client = Groq(api_key=api_key)
            self._api_available = True
            self._initialized = True
            logger.info("Groq client initialized successfully")
            
        except ImportError:
            logger.warning("groq package not installed. Run: pip install groq")
            self._api_available = False
            self._initialized = True
            
        except Exception as e:
            logger.warning(f"Failed to initialize Groq client: {e}. Using keyword fallback.")
            self._api_available = False
            self._initialized = True
    
    def detect(self, text: str, threshold: float = 0.5) -> List[Detection]:
        """
        Detect toxic content in text using Llama Guard 3.
        
        Args:
            text: Input text to analyze
            threshold: Not used for Llama Guard (binary safe/unsafe)
            
        Returns:
            List of Detection objects for toxic content found
        """
        self._init_client()
        
        if not self._api_available:
            return self._detect_keywords(text)
        
        return self._detect_llama_guard(text)
    
    def _detect_llama_guard(self, text: str) -> List[Detection]:
        """Detect using Llama Guard 3 via Groq API."""
        detections = []
        
        try:
            # Call Llama Guard 3
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                max_tokens=100,
                temperature=0.0,
            )
            
            # Parse response
            result = response.choices[0].message.content.strip()
            logger.debug(f"Llama Guard response: {result}")
            
            # Llama Guard returns "safe" or "unsafe\nSX" where X is category
            if result.lower().startswith("safe"):
                return []  # No detections
            
            # Parse unsafe response
            lines = result.strip().split("\n")
            
            if len(lines) >= 1 and lines[0].lower() == "unsafe":
                # Extract categories (S1, S2, etc.)
                categories_found = []
                
                for line in lines[1:]:
                    line = line.strip()
                    # Handle formats like "S1", "S1,S2", "S1, S2"
                    parts = [p.strip() for p in line.replace(",", " ").split()]
                    for part in parts:
                        if part.upper().startswith("S") and part.upper() in LLAMA_GUARD_CATEGORY_MAP:
                            categories_found.append(part.upper())
                
                # If no specific category found but marked unsafe
                if not categories_found:
                    categories_found = ["S10"]  # Default to hate
                
                # Create detections for each category
                for cat_code in categories_found:
                    cat_name, our_category, severity = LLAMA_GUARD_CATEGORY_MAP.get(
                        cat_code, 
                        ("unknown", Category.TOXIC_PROFANITY, Severity.MEDIUM)
                    )
                    
                    detections.append(Detection(
                        category=our_category,
                        severity=severity,
                        confidence=0.95,  # Llama Guard is high confidence
                        matched_text=text[:100] + "..." if len(text) > 100 else text,
                        start_pos=0,
                        end_pos=len(text),
                        explanation=CATEGORY_EXPLANATIONS.get(cat_code, f"Unsafe content detected ({cat_code})"),
                        detector=f"{self.name}_{cat_code}"
                    ))
            
            return detections
            
        except Exception as e:
            logger.error(f"Llama Guard API error: {e}")
            # Fall back to keywords on API error
            return self._detect_keywords(text)
    
    def _detect_keywords(self, text: str) -> List[Detection]:
        """Fallback keyword-based detection."""
        detections = []
        text_lower = text.lower()
        
        for category, keywords in self._toxic_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    start = text_lower.find(keyword)
                    end = start + len(keyword)
                    
                    severity = {
                        Category.TOXIC_HATE: Severity.CRITICAL,
                        Category.TOXIC_VIOLENCE: Severity.CRITICAL,
                        Category.TOXIC_SELF_HARM: Severity.CRITICAL,
                        Category.TOXIC_SEXUAL: Severity.HIGH,
                        Category.TOXIC_HARASSMENT: Severity.HIGH,
                        Category.TOXIC_PROFANITY: Severity.MEDIUM,
                    }.get(category, Severity.MEDIUM)
                    
                    detections.append(Detection(
                        category=category,
                        severity=severity,
                        confidence=0.70,
                        matched_text=text[start:end],
                        start_pos=start,
                        end_pos=end,
                        explanation=f"Toxic keyword detected: '{keyword}'",
                        detector="toxicity_keyword_fallback"
                    ))
        
        # Deduplicate - keep one per category
        seen_categories = {}
        for d in detections:
            if d.category not in seen_categories:
                seen_categories[d.category] = d
        
        return list(seen_categories.values())
