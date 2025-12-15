"""
Restrictor Engine - Main orchestration layer.

Combines all detectors and policy logic to produce final decisions.
This is the primary interface for users of the library.
"""

import hashlib
import time
import logging
from typing import List, Optional
from datetime import datetime

from .models import (
    Decision, Detection, Action, Category, Severity, PolicyConfig
)
from .detectors import PIIDetector, ToxicityDetector, PromptInjectionDetector

logger = logging.getLogger(__name__)


class Restrictor:
    """
    Main content restriction engine.
    
    Usage:
        restrictor = Restrictor()
        decision = restrictor.analyze("Some text to check")
        
        if decision.action == Action.BLOCK:
            print("Content blocked!")
        elif decision.action == Action.REDACT:
            print(f"Safe version: {decision.redacted_text}")
    """
    
    def __init__(
        self, 
        config: Optional[PolicyConfig] = None,
        use_gpu: bool = False,
        lazy_load: bool = True
    ):
        """
        Initialize the Restrictor.
        
        Args:
            config: Policy configuration. Uses defaults if not provided.
            use_gpu: Whether to use GPU for ML models (requires CUDA)
            lazy_load: If True, load ML models only when first needed
        """
        self.config = config or PolicyConfig()
        self.use_gpu = use_gpu
        self.lazy_load = lazy_load
        
        # Initialize detectors
        self._pii_detector: Optional[PIIDetector] = None
        self._toxicity_detector: Optional[ToxicityDetector] = None
        self._injection_detector: Optional[PromptInjectionDetector] = None
        
        if not lazy_load:
            self._init_detectors()
    
    def _init_detectors(self):
        """Initialize all detectors."""
        if self.config.detect_pii and not self._pii_detector:
            self._pii_detector = PIIDetector()
        
        if self.config.detect_toxicity and not self._toxicity_detector:
            self._toxicity_detector = ToxicityDetector(use_gpu=self.use_gpu)
        
        if self.config.detect_prompt_injection and not self._injection_detector:
            self._injection_detector = PromptInjectionDetector()
    
    @property
    def pii_detector(self) -> PIIDetector:
        if not self._pii_detector:
            self._pii_detector = PIIDetector()
        return self._pii_detector
    
    @property
    def toxicity_detector(self) -> ToxicityDetector:
        if not self._toxicity_detector:
            self._toxicity_detector = ToxicityDetector(use_gpu=self.use_gpu)
        return self._toxicity_detector
    
    @property
    def injection_detector(self) -> PromptInjectionDetector:
        if not self._injection_detector:
            self._injection_detector = PromptInjectionDetector()
        return self._injection_detector
    
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
        request_id = Decision.create_request_id()
        
        all_detections: List[Detection] = []
        
        # Run detectors
        if self.config.detect_pii:
            pii_detections = self.pii_detector.detect(text)
            
            # Filter by configured PII types if specified
            if self.config.pii_types:
                pii_detections = [
                    d for d in pii_detections 
                    if d.category in self.config.pii_types
                ]
            
            # Filter by confidence threshold
            pii_detections = [
                d for d in pii_detections 
                if d.confidence >= self.config.pii_confidence_threshold
            ]
            
            all_detections.extend(pii_detections)
        
        if self.config.detect_toxicity:
            toxicity_detections = self.toxicity_detector.detect(
                text, 
                threshold=self.config.toxicity_threshold
            )
            all_detections.extend(toxicity_detections)
        
        if self.config.detect_prompt_injection:
            injection_detections = self.injection_detector.detect(text)
            all_detections.extend(injection_detections)
        
        # Check custom blocked terms
        for term in self.config.blocked_terms:
            if term.lower() in text.lower():
                start = text.lower().find(term.lower())
                all_detections.append(Detection(
                    category=Category.CUSTOM,
                    severity=Severity.HIGH,
                    confidence=1.0,
                    matched_text=text[start:start+len(term)],
                    start_pos=start,
                    end_pos=start + len(term),
                    explanation=f"Custom blocked term: {term}",
                    detector="custom_blocklist"
                ))
        
        # Determine action
        action = self._determine_action(all_detections)
        
        # Generate redacted text if needed
        redacted_text = None
        if action == Action.REDACT and all_detections:
            redacted_text = self._redact_text(text, all_detections)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Generate input hash for audit (don't store raw content)
        input_hash = hashlib.sha256(text.encode()).hexdigest()
        
        return Decision(
            action=action,
            detections=all_detections,
            input_hash=input_hash,
            timestamp=datetime.utcnow(),
            request_id=request_id,
            processing_time_ms=processing_time_ms,
            redacted_text=redacted_text
        )
    
    def _determine_action(self, detections: List[Detection]) -> Action:
        """Determine the appropriate action based on detections."""
        
        if not detections:
            return Action.ALLOW
        
        # Check for critical/blocking detections
        has_toxicity = any(
            d.category.value.startswith("toxic") for d in detections
        )
        has_injection = any(
            d.category in [Category.PROMPT_INJECTION, Category.JAILBREAK_ATTEMPT, Category.DATA_EXFILTRATION]
            for d in detections
        )
        has_pii = any(
            d.category.value.startswith("pii") for d in detections
        )
        
        # Apply policy
        if has_injection and self.config.prompt_injection_action == Action.BLOCK:
            return Action.BLOCK
        
        if has_toxicity and self.config.toxicity_action == Action.BLOCK:
            # Check severity
            max_toxicity_severity = max(
                (d.severity for d in detections if d.category.value.startswith("toxic")),
                default=Severity.LOW,
                key=lambda s: list(Severity).index(s)
            )
            if max_toxicity_severity in [Severity.HIGH, Severity.CRITICAL]:
                return Action.BLOCK
            else:
                return Action.ALLOW_WITH_WARNING
        
        if has_pii:
            if self.config.pii_action == Action.BLOCK:
                # Only block for high-severity PII
                max_pii_severity = max(
                    (d.severity for d in detections if d.category.value.startswith("pii")),
                    default=Severity.LOW,
                    key=lambda s: list(Severity).index(s)
                )
                if max_pii_severity in [Severity.HIGH, Severity.CRITICAL]:
                    return Action.BLOCK
            elif self.config.pii_action == Action.REDACT:
                return Action.REDACT
        
        # Default: if we have any detections but no blocking rules triggered
        max_severity = max(
            detections, 
            key=lambda d: list(Severity).index(d.severity)
        ).severity
        
        if max_severity in [Severity.CRITICAL]:
            return Action.BLOCK
        elif max_severity in [Severity.HIGH]:
            return Action.ALLOW_WITH_WARNING
        else:
            return Action.ALLOW_WITH_WARNING
    
    def _redact_text(self, text: str, detections: List[Detection]) -> str:
        """
        Redact detected content from text.
        
        Only redacts PII detections, not toxicity (which is blocked entirely).
        """
        # Sort detections by position (descending) to redact from end
        pii_detections = [
            d for d in detections 
            if d.category.value.startswith("pii")
        ]
        pii_detections.sort(key=lambda d: d.start_pos, reverse=True)
        
        redacted = text
        for detection in pii_detections:
            replacement = self.config.redact_replacement
            redacted = (
                redacted[:detection.start_pos] + 
                replacement + 
                redacted[detection.end_pos:]
            )
        
        return redacted
    
    def analyze_batch(self, texts: List[str]) -> List[Decision]:
        """
        Analyze multiple texts.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of Decision objects (same order as input)
        """
        return [self.analyze(text) for text in texts]
    
    def get_stats(self) -> dict:
        """Return detector statistics for monitoring."""
        return {
            "config": {
                "detect_pii": self.config.detect_pii,
                "detect_toxicity": self.config.detect_toxicity,
                "detect_prompt_injection": self.config.detect_prompt_injection,
                "toxicity_threshold": self.config.toxicity_threshold,
                "pii_confidence_threshold": self.config.pii_confidence_threshold,
            },
            "detectors_loaded": {
                "pii": self._pii_detector is not None,
                "toxicity": self._toxicity_detector is not None,
                "prompt_injection": self._injection_detector is not None,
            }
        }
