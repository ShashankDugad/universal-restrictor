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
from .detectors.toxicity import get_llm


class Restrictor:
    """
    Main engine for content restriction and safety.
    
    Args:
        policy: PolicyConfig for detection settings (also accepts 'config' alias)
    """
    
    def __init__(self, policy: PolicyConfig = None, config: PolicyConfig = None):
        # Support both 'policy' and 'config' parameter names
        self.policy = policy or config or PolicyConfig()
        
        # Pre-load Llama Guard model
        get_llm()
        
        # Initialize detectors
        self.pii_detector = PIIDetector()
        self.toxicity_detector = ToxicityDetector()
        self.prompt_injection_detector = PromptInjectionDetector()
        self.finance_detector = FinanceIntentDetector()
    
    def analyze(self, text: str, context: Optional[dict] = None, policy: PolicyConfig = None) -> Decision:
        """
        Analyze text and return a decision.
        
        Args:
            text: Text to analyze
            context: Optional context (user_id, conversation_id, etc.)
            policy: Optional policy override for this request
            
        Returns:
            Decision object with action, detections, and metadata
        """
        start_time = time.time()
        
        # Use provided policy or instance default
        policy = policy or self.policy
        
        all_detections: List[Detection] = []
        pii_detections: List[Detection] = []
        
        # Run PII detection
        if policy.detect_pii:
            pii_detections = self.pii_detector.detect(text)
            
            # Filter by confidence threshold
            pii_detections = [
                d for d in pii_detections 
                if d.confidence >= policy.pii_confidence_threshold
            ]
            
            # Filter by PII types if specified
            if policy.pii_types:
                pii_detections = [
                    d for d in pii_detections 
                    if d.category.value in policy.pii_types
                ]
            
            all_detections.extend(pii_detections)
        
        # Run toxicity detection
        if policy.detect_toxicity:
            toxicity_detections = self.toxicity_detector.detect(
                text, 
                threshold=policy.toxicity_threshold
            )
            all_detections.extend(toxicity_detections)
        
        # Run prompt injection detection
        if policy.detect_prompt_injection:
            injection_detections = self.prompt_injection_detector.detect(text)
            # Filter by threshold
            injection_detections = [
                d for d in injection_detections
                if d.confidence >= policy.prompt_injection_threshold
            ]
            all_detections.extend(injection_detections)
        
        # Run finance intent detection
        if policy.detect_finance_intent:
            finance_detections = self.finance_detector.detect(text)
            all_detections.extend(finance_detections)
        
        # Determine action based on detections and policy
        action = self._determine_action(all_detections, policy)
        
        # Generate redacted text if needed
        redacted_text = None
        if action == Action.REDACT and pii_detections:
            redacted_text = self.pii_detector.redact(
                text, 
                pii_detections, 
                replacement=policy.redact_replacement
            )
        
        # Calculate metadata
        processing_time = (time.time() - start_time) * 1000
        input_hash = hashlib.sha256(text.encode()).hexdigest()
        categories_found = list(set(d.category for d in all_detections))
        max_severity = self._get_max_severity(all_detections)
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
    
    def _get_max_severity(self, detections: List[Detection]) -> Optional[Severity]:
        """Get the highest severity from detections."""
        if not detections:
            return None
        
        severity_order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        max_idx = -1
        max_sev = None
        
        for d in detections:
            try:
                idx = severity_order.index(d.severity)
                if idx > max_idx:
                    max_idx = idx
                    max_sev = d.severity
            except ValueError:
                pass
        
        return max_sev
    
    def _determine_action(self, detections: List[Detection], policy: PolicyConfig) -> Action:
        """Determine action based on detections and policy."""
        if not detections:
            return Action.ALLOW
        
        # Check for blocking conditions first (highest priority)
        for d in detections:
            # Prompt injection
            if d.category in [Category.PROMPT_INJECTION, Category.JAILBREAK_ATTEMPT]:
                return policy.prompt_injection_action
            
            # Toxicity
            if d.category in [Category.TOXIC_HATE, Category.TOXIC_VIOLENCE, Category.TOXIC_SELF_HARM]:
                return policy.toxicity_action
            
            # Insider info (always block)
            if d.category == Category.FINANCE_INSIDER_INFO:
                return Action.BLOCK
        
        # Check for finance intent (warning)
        for d in detections:
            if d.category in [
                Category.FINANCE_TRADING_INTENT,
                Category.FINANCE_INVESTMENT_ADVICE,
                Category.FINANCE_LOAN_DISCUSSION
            ]:
                return policy.finance_intent_action
        
        # Check for PII (redact)
        has_pii = any(d.category.value.startswith('pii_') for d in detections)
        if has_pii:
            return policy.pii_action
        
        # Default for other detections
        if detections:
            return Action.ALLOW_WITH_WARNING
        
        return Action.ALLOW
    
    def analyze_batch(self, texts: List[str], policy: PolicyConfig = None) -> List[Decision]:
        """Analyze multiple texts."""
        return [self.analyze(text, policy=policy) for text in texts]
