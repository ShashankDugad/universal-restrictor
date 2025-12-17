"""
Main Restrictor engine - orchestrates all detectors.

Detection Pipeline:
1. PII Detection (regex) - fast
2. Finance Intent Detection (regex) - fast
3. Prompt Injection Detection (regex) - fast
4. Toxicity Detection:
   a. Keywords (obvious threats) - fast
   b. Escalation Classifier (suspicious patterns) - fast
   c. Claude API (only if escalated) - premium
"""

import hashlib
import time
import logging
from typing import List, Optional
from datetime import datetime

from .models import (
    Detection, Decision, Action, Severity, Category, PolicyConfig
)
from .detectors import PIIDetector, ToxicityDetector, PromptInjectionDetector, FinanceIntentDetector
from .detectors.toxicity import get_llm
from .detectors.escalation_classifier import EscalationClassifier
from .detectors.claude_detector import ClaudeDetector

logger = logging.getLogger(__name__)


class Restrictor:
    """
    Main engine for content restriction and safety.
    
    Args:
        policy: PolicyConfig for detection settings
        enable_claude: Enable Claude API for premium detection (default: True if key exists)
    """
    
    def __init__(
        self, 
        policy: PolicyConfig = None, 
        config: PolicyConfig = None,
        enable_claude: bool = None
    ):
        self.policy = policy or config or PolicyConfig()
        
        # Pre-load Llama Guard model
        get_llm()
        
        # Initialize detectors
        self.pii_detector = PIIDetector()
        self.toxicity_detector = ToxicityDetector()
        self.prompt_injection_detector = PromptInjectionDetector()
        self.finance_detector = FinanceIntentDetector()
        
        # Escalation pipeline
        self.escalation_classifier = EscalationClassifier()
        self.claude_detector = ClaudeDetector()
        
        # Auto-enable Claude if API key exists
        if enable_claude is None:
            self.enable_claude = self.claude_detector.is_available()
        else:
            self.enable_claude = enable_claude and self.claude_detector.is_available()
        
        if self.enable_claude:
            logger.info("Claude API enabled for premium detection")
        else:
            logger.info("Claude API disabled - using local detection only")
    
    def analyze(self, text: str, context: Optional[dict] = None, policy: PolicyConfig = None) -> Decision:
        """Analyze text and return a decision."""
        start_time = time.time()
        
        policy = policy or self.policy
        
        all_detections: List[Detection] = []
        pii_detections: List[Detection] = []
        
        # 1. Run PII detection first
        if policy.detect_pii:
            pii_detections = self.pii_detector.detect(text)
            pii_detections = [
                d for d in pii_detections 
                if d.confidence >= policy.pii_confidence_threshold
            ]
            if policy.pii_types:
                pii_detections = [
                    d for d in pii_detections 
                    if d.category.value in policy.pii_types
                ]
            all_detections.extend(pii_detections)
        
        # 2. Run prompt injection detection
        if policy.detect_prompt_injection:
            injection_detections = self.prompt_injection_detector.detect(text)
            injection_detections = [
                d for d in injection_detections
                if d.confidence >= policy.prompt_injection_threshold
            ]
            all_detections.extend(injection_detections)
        
        # 3. Run finance intent detection
        if policy.detect_finance_intent:
            finance_detections = self.finance_detector.detect(text)
            all_detections.extend(finance_detections)
        
        # 4. Run toxicity detection (skip if PII/finance found)
        has_pii = len(pii_detections) > 0
        has_finance = any(d.category.value.startswith('finance_') for d in all_detections)
        
        if policy.detect_toxicity and not has_pii and not has_finance:
            # 4a. Try keyword detection first (fast)
            toxicity_detections = self.toxicity_detector.detect(
                text, 
                threshold=policy.toxicity_threshold
            )
            
            # 4b. If no keyword hits, check escalation classifier
            if not toxicity_detections:
                escalation = self.escalation_classifier.classify(text)
                
                if escalation.needs_escalation and self.enable_claude:
                    # 4c. Use Claude API for suspicious text
                    context_str = f"Triggered patterns: {escalation.triggered_patterns}"
                    claude_detections = self.claude_detector.detect(text, context=context_str)
                    toxicity_detections.extend(claude_detections)
            
            all_detections.extend(toxicity_detections)
        
        # Determine action
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
        
        # Check for blocking conditions first
        for d in detections:
            if d.category in [Category.PROMPT_INJECTION, Category.JAILBREAK_ATTEMPT]:
                return policy.prompt_injection_action
            
            if d.category in [Category.TOXIC_HATE, Category.TOXIC_VIOLENCE, 
                              Category.TOXIC_SELF_HARM, Category.TOXIC_HARASSMENT,
                              Category.TOXIC_SEXUAL]:
                return policy.toxicity_action
            
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
        
        if detections:
            return Action.ALLOW_WITH_WARNING
        
        return Action.ALLOW
    
    def analyze_batch(self, texts: List[str], policy: PolicyConfig = None) -> List[Decision]:
        """Analyze multiple texts."""
        return [self.analyze(text, policy=policy) for text in texts]
    
    def get_api_usage(self) -> dict:
        """Get Claude API usage stats."""
        return self.claude_detector.get_cost_estimate()
