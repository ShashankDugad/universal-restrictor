"""
Main Restrictor engine - orchestrates all detectors.
"""

import hashlib
import time
from typing import List, Optional
from datetime import datetime

from .models import (
    Detection, Decision, Action, Severity, Category, PolicyConfig
)
from .detectors import PIIDetector, ToxicityDetector, PromptInjectionDetector, FinanceIntentDetector


class Restrictor:
    """
    Main engine for content restriction and safety.
    
    Orchestrates multiple detectors:
    - PII Detection (regex-based)
    - Toxicity Detection (Llama Guard 4)
    - Prompt Injection Detection (pattern-based)
    - Finance Intent Detection (India-specific)
    """
    
    def __init__(self, policy: PolicyConfig = None):
        self.policy = policy or PolicyConfig()
        
        # Initialize detectors
        self.pii_detector = PIIDetector()
        self.toxicity_detector = ToxicityDetector()
        self.prompt_injection_detector = PromptInjectionDetector()
        self.finance_detector = FinanceIntentDetector()
    
    def analyze(self, text: str, context: Optional[dict] = None) -> Decision:
        """
        Analyze text and return a decision.
        
        Args:
            text: The text to analyze
            context: Optional context (e.g., user_id, conversation_id)
            
        Returns:
            Decision object with action, detections, and optional redacted text
        """
        start_time = time.time()
        
        all_detections: List[Detection] = []
        
        # Run PII detection
        pii_detections = self.pii_detector.detect(text)
        all_detections.extend(pii_detections)
        
        # Run toxicity detection
        toxicity_detections = self.toxicity_detector.detect(text)
        all_detections.extend(toxicity_detections)
        
        # Run prompt injection detection
        injection_detections = self.prompt_injection_detector.detect(text)
        all_detections.extend(injection_detections)
        
        # Run finance intent detection
        finance_detections = self.finance_detector.detect(text)
        all_detections.extend(finance_detections)
        
        # Determine action based on detections
        action = self._determine_action(all_detections)
        
        # Generate redacted text if needed
        redacted_text = None
        if action == Action.REDACT:
            redacted_text = self.pii_detector.redact(text, pii_detections)
        
        # Calculate metadata
        processing_time = (time.time() - start_time) * 1000
        input_hash = hashlib.sha256(text.encode()).hexdigest()
        categories_found = list(set(d.category for d in all_detections))
        max_severity = max((d.severity for d in all_detections), default=None, key=lambda s: list(Severity).index(s) if s else -1)
        max_confidence = max((d.confidence for d in all_detections), default=0.0)
        
        return Decision(
            action=action,
            detections=all_detections,
            input_hash=input_hash,
            timestamp=datetime.utcnow(),
            processing_time_ms=processing_time,
            categories_found=categories_found,
            max_severity=max_severity,
            max_confidence=max_confidence,
            redacted_text=redacted_text
        )
    
    def _determine_action(self, detections: List[Detection]) -> Action:
        """Determine action based on detections."""
        if not detections:
            return Action.ALLOW
        
        # Check for blocking conditions
        for d in detections:
            # Block on prompt injection
            if d.category in [Category.PROMPT_INJECTION, Category.JAILBREAK_ATTEMPT]:
                return Action.BLOCK
            
            # Block on critical toxicity
            if d.category in [Category.TOXIC_HATE, Category.TOXIC_VIOLENCE, Category.TOXIC_SELF_HARM]:
                return Action.BLOCK
            
            # Block on insider info (compliance critical)
            if d.category == Category.FINANCE_INSIDER_INFO:
                return Action.BLOCK
        
        # Check for warning conditions (finance intent)
        for d in detections:
            if d.category in [
                Category.FINANCE_TRADING_INTENT,
                Category.FINANCE_INVESTMENT_ADVICE,
                Category.FINANCE_LOAN_DISCUSSION
            ]:
                return Action.ALLOW_WITH_WARNING
        
        # Check for redaction (PII)
        has_pii = any(d.category.value.startswith('pii_') for d in detections)
        if has_pii:
            return Action.REDACT
        
        # Default: allow with warning for other detections
        if detections:
            return Action.ALLOW_WITH_WARNING
        
        return Action.ALLOW
    
    def analyze_batch(self, texts: List[str]) -> List[Decision]:
        """Analyze multiple texts."""
        return [self.analyze(text) for text in texts]
