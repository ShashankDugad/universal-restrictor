"""
Toxicity Detector - Unified detection pipeline.

Pipeline order:
1. Keywords (instant, high-confidence patterns)
2. MoE Model (2-stage MuRIL)
3. Claude API (edge cases, low confidence)
"""
import re
import logging
from typing import List, Optional, Tuple
from enum import Enum

from restrictor.models import Detection, Category, Severity

logger = logging.getLogger(__name__)


# =============================================================================
# KEYWORD PATTERNS (Fast, high-confidence)
# =============================================================================

THREAT_PATTERNS: List[Tuple[str, Category, Severity, str]] = [
    # === DIRECT VIOLENCE ===
    (r'(?i)\b(i\s+will\s+kill\s+you|i\'?m\s+going\s+to\s+kill\s+you|gonna\s+kill\s+you)',
     Category.TOXIC_VIOLENCE, Severity.CRITICAL, "Direct death threat"),
    (r'(?i)\b(i\s+will\s+murder|i\'?m\s+going\s+to\s+murder|gonna\s+murder)',
     Category.TOXIC_VIOLENCE, Severity.CRITICAL, "Murder threat"),
    (r'(?i)\b(kill\s+yourself|kys\b|go\s+die)',
     Category.TOXIC_SELF_HARM, Severity.CRITICAL, "Encouraging self-harm"),
    (r'(?i)\b(i\s+will\s+shoot|i\'?m\s+going\s+to\s+shoot|gonna\s+shoot)\s*(you|him|her|them)?',
     Category.TOXIC_VIOLENCE, Severity.CRITICAL, "Shooting threat"),
    
    # === HINDI/HINGLISH SLURS ===
    (r'(?i)\b(madarchod|madarc?hod|mc\b|m\.c\.|motherchod)',
     Category.TOXIC_HARASSMENT, Severity.CRITICAL, "Hindi slur - maternal"),
    (r'(?i)\b(bhenchod|behen\s*chod|bc\b|b\.c\.|sister.*chod|benchod)',
     Category.TOXIC_HARASSMENT, Severity.CRITICAL, "Hindi slur - sister"),
    (r'(?i)\b(chutiya|chutiy[ae]|ch[uoo]t)',
     Category.TOXIC_HARASSMENT, Severity.CRITICAL, "Hindi slur - vulgar"),
    (r'(?i)\b(gandu|gaand|g[a@]ndu)',
     Category.TOXIC_HARASSMENT, Severity.CRITICAL, "Hindi slur - vulgar"),
    (r'(?i)\b(randi|r[a@]ndi|randwa)',
     Category.TOXIC_HARASSMENT, Severity.CRITICAL, "Hindi slur - prostitute"),
    (r'(?i)\b(harami|haramkhor|haram\s*zada)',
     Category.TOXIC_HARASSMENT, Severity.HIGH, "Hindi slur - illegitimate"),
    (r'(?i)\b(kutt[ae]|kutta|kuttiya|kutiya)',
     Category.TOXIC_HARASSMENT, Severity.HIGH, "Hindi slur - dog"),
    (r'(?i)\b(bhosdi\s*ke|bhosd[i]?k[e]?|bsdk)',
     Category.TOXIC_HARASSMENT, Severity.CRITICAL, "Hindi slur - vulgar"),
    (r'(?i)\b(lodu|loda|lauda|l[o0]de)',
     Category.TOXIC_HARASSMENT, Severity.CRITICAL, "Hindi slur - vulgar"),
    (r'(?i)\bteri\s*maa\s*ki',
     Category.TOXIC_HARASSMENT, Severity.CRITICAL, "Hindi slur - maternal"),
    (r'(?i)\bteri\s*behen',
     Category.TOXIC_HARASSMENT, Severity.CRITICAL, "Hindi slur - sister"),
    (r'(?i)\b(saala|saale|sala\b|kamina|kameena)',
     Category.TOXIC_HARASSMENT, Severity.MEDIUM, "Hindi slur"),
    (r'(?i)\b(tmkc|bkl|mkc)',
     Category.TOXIC_HARASSMENT, Severity.CRITICAL, "Hindi abbreviation slur"),
    
    # === DANGEROUS CONTENT ===
    (r'(?i)(how\s+to\s+make.*bomb|build.*bomb|homemade\s+explosive)',
     Category.TOXIC_VIOLENCE, Severity.CRITICAL, "Bomb-making"),
    (r'(?i)(how\s+to\s+make.*explosive|explosive\s+device|ied\b)',
     Category.TOXIC_VIOLENCE, Severity.CRITICAL, "Explosive device"),
    (r'(?i)(how\s+to\s+make.*poison|make.*ricin|make.*cyanide)',
     Category.TOXIC_VIOLENCE, Severity.CRITICAL, "Poison-making"),
    (r'(?i)(how\s+to\s+make.*gun|3d.*print.*gun|ghost\s+gun)',
     Category.TOXIC_VIOLENCE, Severity.CRITICAL, "Weapon manufacturing"),
    (r'(?i)(how\s+to\s+make.*meth|cook.*meth|synthesis.*drug)',
     Category.TOXIC_VIOLENCE, Severity.CRITICAL, "Drug manufacturing"),
    (r'(?i)(how\s+to\s+hack|ddos\s+attack|sql\s+injection)',
     Category.TOXIC_HARASSMENT, Severity.HIGH, "Hacking instructions"),
    
    # === HATE SPEECH ===
    (r'(?i)\b(hate\s+all|kill\s+all|exterminate\s+all)\s+\w+',
     Category.TOXIC_HATE, Severity.CRITICAL, "Group hatred/genocide"),
    (r'(?i)\b(subhuman|inferior\s+race|master\s+race)',
     Category.TOXIC_HATE, Severity.CRITICAL, "Racial supremacy"),
    
    # === SELF-HARM ===
    (r'(?i)\b(want\s+to\s+kill\s+myself|end\s+my\s+life|commit\s+suicide)',
     Category.TOXIC_SELF_HARM, Severity.CRITICAL, "Suicidal ideation"),
    (r'(?i)\b(best\s+way\s+to\s+(die|suicide)|painless\s+death)',
     Category.TOXIC_SELF_HARM, Severity.CRITICAL, "Seeking suicide methods"),
]



# =============================================================================
# HINDI SAFE PHRASES (to prevent false positives)
# =============================================================================

HINDI_SAFE_PHRASES = [
    "namaste", "namaskar", "kaise ho", "kaise hain", "kya haal", "kya hal",
    "theek hai", "thik hai", "shukriya", "dhanyavaad", "dhanyavad", 
    "alvida", "phir milenge", "kal milte", "accha", "acha",
    "bahut accha", "bohot badiya", "mast", "sahi hai", "badhiya",
    "shubh prabhat", "shubh ratri", "good morning", "good night",
]

HINDI_SLURS = [
    "chod", "maa ki", "behen", "gandu", "kutt", "bhosdi", "lodu", 
    "randi", "harami", "sala", "kamina", "chut", "lund", "gaand",
]

ENGLISH_SAFE_PHRASES = [
    "went back to my country", "going back to my country", 
    "returned to my country", "visiting my country",
    "traveled to my country", "trip to my country",
    "vacation in my", "holiday in my",
]

def is_safe_phrase(text: str) -> bool:
    """Check if text is a safe phrase (English or Hindi, not combined with slurs)."""
    text_lower = text.lower().strip()
    
    # Check English safe phrases first (no slur check needed)
    if any(phrase in text_lower for phrase in ENGLISH_SAFE_PHRASES):
        return True
    
    # Check if any Hindi safe phrase is present
    has_safe = any(phrase in text_lower for phrase in HINDI_SAFE_PHRASES)
    if not has_safe:
        return False
    
    # Check if any slur is also present
    has_slur = any(slur in text_lower for slur in HINDI_SLURS)
    
    # Safe only if safe phrase present AND no slurs
    return has_safe and not has_slur



def is_gibberish(text: str) -> bool:
    """
    Detect gibberish/nonsense text that should not be analyzed.
    Returns True if text is likely gibberish.
    """
    if not text or len(text) < 2:
        return True
    
    text_lower = text.lower().strip()
    words = text_lower.split()
    
    # Single word checks
    if len(words) == 1:
        word = words[0]
        if len(word) > 3:
            # Check vowel ratio
            vowels = sum(1 for c in word if c in 'aeiou')
            vowel_ratio = vowels / len(word)
            if vowel_ratio < 0.15:
                return True
            
            # Repeated characters
            for i in range(len(word) - 2):
                if word[i] == word[i+1] == word[i+2]:
                    return True
            
            # Too many consonants in a row
            consonant_count = 0
            for c in word:
                if c.isalpha() and c not in 'aeiou':
                    consonant_count += 1
                    if consonant_count >= 4:
                        return True
                else:
                    consonant_count = 0
    
    return False


def get_dynamic_threshold(text: str, base_threshold: float = 0.7) -> float:
    """
    Get confidence threshold based on text length.
    Shorter text needs higher confidence to block.
    """
    word_count = len(text.split())
    
    if word_count <= 3:
        return 0.85
    elif word_count <= 6:
        return 0.80
    elif word_count <= 12:
        return 0.75
    else:
        return base_threshold



class ToxicityDetector:
    """
    Unified toxicity detection using Keywords + MoE + Claude.
    """
    
    def __init__(
        self,
        use_moe: bool = True,
        use_claude: bool = True,
        moe_threshold: float = 0.7,
        claude_threshold: float = 0.5,
    ):
        self.use_moe = use_moe
        self.use_claude = use_claude
        self.moe_threshold = moe_threshold
        self.claude_threshold = claude_threshold
        
        self._moe_detector = None
        self._claude_detector = None
    
    def _get_moe_detector(self):
        """Lazy load MoE detector."""
        if self._moe_detector is None and self.use_moe:
            try:
                from restrictor.detectors.moe_detector import get_moe_detector
                self._moe_detector = get_moe_detector()
                self._moe_detector.load()
            except Exception as e:
                logger.warning(f"Failed to load MoE detector: {e}")
                self._moe_detector = None
        return self._moe_detector
    
    def _get_claude_detector(self):
        """Lazy load Claude detector."""
        if self._claude_detector is None and self.use_claude:
            try:
                from restrictor.detectors.claude_detector import ClaudeDetector
                self._claude_detector = ClaudeDetector()
            except Exception as e:
                logger.warning(f"Failed to load Claude detector: {e}")
                self._claude_detector = None
        return self._claude_detector
    
    def _keyword_detect(self, text: str) -> List[Detection]:
        """Fast keyword-based detection."""
        detections = []
        text_lower = text.lower()
        
        for pattern, category, severity, explanation in THREAT_PATTERNS:
            if re.search(pattern, text):
                detections.append(Detection(
                    category=category,
                    confidence=0.98,
                    severity=severity,
                    detector="keyword",
                    explanation=f"[KEYWORD] {explanation}",
                    start_pos=0,
                    end_pos=len(text),
                    matched_text=text[:100],
                ))
                # Return first match for keywords (they're high confidence)
                return detections
        
        return detections
    
    def _moe_detect(self, text: str) -> List[Detection]:
        """MoE model detection."""
        moe = self._get_moe_detector()
        if moe is None:
            return []
        
        try:
            detections = moe.detect(text)
            # Add [MOE] prefix to explanation
            for d in detections:
                d.explanation = f"[MOE] {d.explanation}"
            return detections
        except Exception as e:
            logger.error(f"MoE detection error: {e}")
            return []
    
    def _claude_detect(self, text: str) -> List[Detection]:
        """Claude API detection for edge cases."""
        claude = self._get_claude_detector()
        if claude is None:
            return []
        
        try:
            detections = claude.detect(text)
            # Add [CLAUDE] prefix to explanation
            for d in detections:
                d.explanation = f"[CLAUDE] {d.explanation}"
            return detections
        except Exception as e:
            logger.error(f"Claude detection error: {e}")
            return []
    
    def detect(self, text: str, threshold: float = None) -> List[Detection]:
        """
        Run full detection pipeline.
        
        Order:
        0. Gibberish filter (instant) - skip nonsense
        1. Safe phrases check (prevent false positives)
        2. Keywords (instant) - if match, return immediately
        3. MoE (fast) - with dynamic threshold based on text length
        4. Claude (slow) - for uncertain cases (confidence 0.6-0.85)
        """
        if not text or not text.strip():
            return []
        
        # 0. Gibberish filter - skip nonsense text
        if is_gibberish(text):
            logger.info(f"✅ GIBBERISH: '{text[:30]}...' - skipping detection")
            return []
        
        # 1. Check for safe Hindi phrases first (prevent false positives)
        if is_safe_phrase(text):
            logger.info(f"✅ SAFE PHRASE: '{text[:30]}...' - skipping detection")
            return []
        
        all_detections = []
        
        # 1. Keyword detection (instant)
        keyword_detections = self._keyword_detect(text)
        if keyword_detections:
            logger.info(f"🔑 KEYWORD MATCH: {keyword_detections[0].explanation}")
            return keyword_detections
        
        # 2. MoE detection with dynamic threshold
        if self.use_moe:
            moe_detections = self._moe_detect(text)
            if moe_detections:
                max_conf = max(d.confidence for d in moe_detections)
                dynamic_thresh = get_dynamic_threshold(text, self.moe_threshold)
                
                if max_conf >= 0.85:
                    # High confidence - block immediately
                    logger.info(f"🤖 MOE HIGH CONF: {moe_detections[0].detector} (conf: {max_conf:.2f}) - blocking")
                    return moe_detections
                elif max_conf >= dynamic_thresh:
                    # Above dynamic threshold - block
                    logger.info(f"🤖 MOE DETECTED: {moe_detections[0].detector} (conf: {max_conf:.2f}, thresh: {dynamic_thresh:.2f})")
                    return moe_detections
                elif max_conf >= 0.60 and self.use_claude:
                    # Uncertain zone (0.60-0.85) - escalate to Claude
                    logger.info(f"🤖 MOE UNCERTAIN: {moe_detections[0].detector} (conf: {max_conf:.2f}) - escalating to Claude")
                    claude_detections = self._claude_detect(text)
                    if claude_detections:
                        logger.info(f"🧠 CLAUDE CONFIRMED: {claude_detections[0].category}")
                        return claude_detections
                    else:
                        logger.info(f"🧠 CLAUDE CLEARED: MoE false positive")
                        return []
                else:
                    # Low confidence - safe
                    logger.info(f"🤖 MOE LOW CONF: {moe_detections[0].detector} (conf: {max_conf:.2f}) - allowing")
                    return []
        
        # 3. Claude for edge cases (only if no MoE detection)
        if self.use_claude:
            claude_detections = self._claude_detect(text)
            if claude_detections:
                logger.info(f"🧠 CLAUDE DETECTED: {claude_detections[0].category}")
                return claude_detections
        
        logger.info(f"✅ SAFE: No threats detected by any layer")
        return []
    
    def detect_with_source(self, text: str) -> Tuple[List[Detection], str]:
        """
        Run detection and return source.
        
        Returns:
            Tuple of (detections, source) where source is 'keyword', 'moe', 'claude', or 'none'
        """
        if not text or not text.strip():
            return [], "none"
        
        # 1. Keyword detection
        keyword_detections = self._keyword_detect(text)
        if keyword_detections:
            logger.info(f"🔑 KEYWORD MATCH: {keyword_detections[0].explanation}")
            return keyword_detections, "keyword"
        
        # 2. MoE detection
        if self.use_moe:
            moe_detections = self._moe_detect(text)
            if moe_detections:
                max_conf = max(d.confidence for d in moe_detections)
                if max_conf >= self.moe_threshold:
                    logger.info(f"🤖 MOE DETECTED: {moe_detections[0].detector} (conf: {max_conf:.2f})")
                    return moe_detections, "moe"
        
        # 3. Claude for edge cases
        if self.use_claude:
            claude_detections = self._claude_detect(text)
            if claude_detections:
                logger.info(f"🧠 CLAUDE DETECTED: {claude_detections[0].category}")
                return claude_detections, "claude"
        
        logger.info(f"✅ SAFE: No threats detected")
        return [], "none"


# Singleton
_toxicity_detector: Optional[ToxicityDetector] = None


def get_toxicity_detector() -> ToxicityDetector:
    """Get or create toxicity detector singleton."""
    global _toxicity_detector
    if _toxicity_detector is None:
        _toxicity_detector = ToxicityDetector()
    return _toxicity_detector

# Hindi safe phrases that should never be flagged
HINDI_SAFE_PHRASES = [
    "namaste", "namaskar", "kaise ho", "kaise hain", "kya haal",
    "theek hai", "shukriya", "dhanyavaad", "alvida", "phir milenge",
    "accha", "bahut accha", "bohot badiya", "mast", "sahi hai",
]

def is_safe_hindi(text: str) -> bool:
    """Check if text is a safe Hindi phrase."""
    text_lower = text.lower().strip()
    for phrase in HINDI_SAFE_PHRASES:
        if phrase in text_lower:
            # Check it's not combined with slurs
            slurs = ["chod", "maa", "behen", "gandu", "kutt", "bhosdi", "lodu", "randi"]
            if not any(slur in text_lower for slur in slurs):
                return True
    return False
