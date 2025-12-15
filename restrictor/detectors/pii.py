"""
PII Detector - Pattern-based detection for personally identifiable information.

Supports:
- International: Email, phone, credit card, SSN, IP address
- India-specific: Aadhaar, PAN, Indian phone numbers
- Secrets: API keys, passwords in common formats

Uses regex for speed. ML-based NER can be layered on top for names/addresses.
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass

from ..models import Detection, Category, Severity


@dataclass
class PIIPattern:
    """Definition of a PII pattern to detect."""
    category: Category
    pattern: re.Pattern
    severity: Severity
    confidence: float  # Base confidence for regex match
    explanation: str
    validator: Optional[callable] = None  # Optional validation function


class PIIDetector:
    """
    Detect PII using regex patterns.
    
    Fast, deterministic, no ML dependencies.
    Layered approach: regex first, then optional NER for names/addresses.
    """
    
    def __init__(self):
        self.patterns = self._build_patterns()
        self.name = "pii_regex"
    
    def _build_patterns(self) -> List[PIIPattern]:
        """Build all PII detection patterns."""
        
        patterns = []
        
        # Email
        patterns.append(PIIPattern(
            category=Category.PII_EMAIL,
            pattern=re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                re.IGNORECASE
            ),
            severity=Severity.MEDIUM,
            confidence=0.95,
            explanation="Email address detected"
        ))
        
        # Phone - International format
        patterns.append(PIIPattern(
            category=Category.PII_PHONE,
            pattern=re.compile(
                r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
            ),
            severity=Severity.MEDIUM,
            confidence=0.85,
            explanation="Phone number detected"
        ))
        
        # Phone - Indian format (10 digits starting with 6-9)
        patterns.append(PIIPattern(
            category=Category.PII_PHONE,
            pattern=re.compile(
                r'(?:\+91[-.\s]?)?[6-9]\d{9}\b'
            ),
            severity=Severity.MEDIUM,
            confidence=0.90,
            explanation="Indian phone number detected"
        ))
        
        # Credit Card (Luhn validation recommended but not required)
        patterns.append(PIIPattern(
            category=Category.PII_CREDIT_CARD,
            pattern=re.compile(
                r'\b(?:4[0-9]{12}(?:[0-9]{3})?|'  # Visa
                r'5[1-5][0-9]{14}|'               # MasterCard
                r'3[47][0-9]{13}|'                # Amex
                r'6(?:011|5[0-9]{2})[0-9]{12})\b' # Discover
            ),
            severity=Severity.CRITICAL,
            confidence=0.90,
            explanation="Credit card number detected",
            validator=self._validate_luhn
        ))
        
        # Credit card with spaces/dashes
        patterns.append(PIIPattern(
            category=Category.PII_CREDIT_CARD,
            pattern=re.compile(
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
            ),
            severity=Severity.CRITICAL,
            confidence=0.85,
            explanation="Credit card number detected (with separators)"
        ))
        
        # SSN (US)
        patterns.append(PIIPattern(
            category=Category.PII_SSN,
            pattern=re.compile(
                r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'
            ),
            severity=Severity.CRITICAL,
            confidence=0.80,
            explanation="US Social Security Number detected"
        ))
        
        # Aadhaar (Indian 12-digit ID)
        patterns.append(PIIPattern(
            category=Category.PII_AADHAAR,
            pattern=re.compile(
                r'\b[2-9]\d{3}[-\s]?\d{4}[-\s]?\d{4}\b'
            ),
            severity=Severity.CRITICAL,
            confidence=0.85,
            explanation="Aadhaar number detected",
            validator=self._validate_aadhaar
        ))
        
        # PAN (Indian tax ID - AAAAA0000A format: 5 letters + 4 digits + 1 letter)
        patterns.append(PIIPattern(
            category=Category.PII_PAN,
            pattern=re.compile(
                r'\b[A-Z]{5}\d{4}[A-Z]\b',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=0.90,
            explanation="PAN card number detected"
        ))
        
        # IP Address (IPv4)
        patterns.append(PIIPattern(
            category=Category.PII_IP_ADDRESS,
            pattern=re.compile(
                r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
                r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
            ),
            severity=Severity.LOW,
            confidence=0.95,
            explanation="IP address detected"
        ))
        
        # API Keys (common patterns)
        patterns.append(PIIPattern(
            category=Category.PII_API_KEY,
            pattern=re.compile(
                r'\b(?:sk-[a-zA-Z0-9]{32,}|'           # OpenAI
                r'sk-ant-[a-zA-Z0-9-]{32,}|'          # Anthropic
                r'AIza[0-9A-Za-z_-]{35}|'             # Google
                r'AKIA[0-9A-Z]{16}|'                  # AWS Access Key
                r'ghp_[a-zA-Z0-9]{36}|'               # GitHub
                r'xox[baprs]-[0-9a-zA-Z-]{10,})\b'    # Slack
            ),
            severity=Severity.CRITICAL,
            confidence=0.95,
            explanation="API key or secret detected"
        ))
        
        # Generic secret patterns
        patterns.append(PIIPattern(
            category=Category.PII_PASSWORD,
            pattern=re.compile(
                r'(?i)(?:password|passwd|pwd|secret|token|api_key|apikey|auth)'
                r'\s*[:=]\s*["\']?([^\s"\']{8,})["\']?'
            ),
            severity=Severity.CRITICAL,
            confidence=0.80,
            explanation="Password or secret in key=value format detected"
        ))
        
        # Passport (generic format)
        patterns.append(PIIPattern(
            category=Category.PII_PASSPORT,
            pattern=re.compile(
                r'\b[A-Z]{1,2}[0-9]{6,9}\b'
            ),
            severity=Severity.HIGH,
            confidence=0.60,  # Lower confidence - many false positives
            explanation="Possible passport number detected"
        ))
        
        return patterns
    
    def _validate_luhn(self, number: str) -> bool:
        """Validate credit card number using Luhn algorithm."""
        digits = [int(d) for d in re.sub(r'[-\s]', '', number)]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        
        total = sum(odd_digits)
        for d in even_digits:
            d *= 2
            if d > 9:
                d -= 9
            total += d
        
        return total % 10 == 0
    
    def _validate_aadhaar(self, number: str) -> bool:
        """Basic Aadhaar validation (Verhoeff algorithm is more accurate)."""
        digits = re.sub(r'[-\s]', '', number)
        if len(digits) != 12:
            return False
        # First digit can't be 0 or 1
        if digits[0] in '01':
            return False
        return True
    
    def detect(self, text: str) -> List[Detection]:
        """
        Detect all PII in the given text.
        
        Args:
            text: Input text to scan
            
        Returns:
            List of Detection objects for each PII found
        """
        detections = []
        
        for pii_pattern in self.patterns:
            for match in pii_pattern.pattern.finditer(text):
                matched_text = match.group()
                
                # Apply validator if exists
                confidence = pii_pattern.confidence
                if pii_pattern.validator:
                    if not pii_pattern.validator(matched_text):
                        confidence *= 0.5  # Reduce confidence if validation fails
                
                detections.append(Detection(
                    category=pii_pattern.category,
                    severity=pii_pattern.severity,
                    confidence=confidence,
                    matched_text=matched_text,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    explanation=pii_pattern.explanation,
                    detector=self.name
                ))
        
        # Deduplicate overlapping detections (keep highest confidence)
        detections = self._deduplicate(detections)
        
        return detections
    
    def _deduplicate(self, detections: List[Detection]) -> List[Detection]:
        """Remove overlapping detections, keeping highest confidence."""
        if not detections:
            return []
        
        # Sort by start position, then by confidence (descending)
        sorted_detections = sorted(
            detections, 
            key=lambda d: (d.start_pos, -d.confidence)
        )
        
        result = []
        last_end = -1
        
        for detection in sorted_detections:
            if detection.start_pos >= last_end:
                result.append(detection)
                last_end = detection.end_pos
            elif detection.confidence > result[-1].confidence:
                # Replace if higher confidence and overlapping
                result[-1] = detection
                last_end = detection.end_pos
        
        return result
