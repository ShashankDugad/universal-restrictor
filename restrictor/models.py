"""
Data models for Universal Restrictor.

These models define the structure of detection results and decisions.
Designed for auditability and compliance logging.
"""

from enum import Enum
from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class Category(str, Enum):
    """Categories of detected content."""
    
    # PII Categories
    PII_NAME = "pii_name"
    PII_EMAIL = "pii_email"
    PII_PHONE = "pii_phone"
    PII_ADDRESS = "pii_address"
    PII_SSN = "pii_ssn"
    PII_CREDIT_CARD = "pii_credit_card"
    PII_AADHAAR = "pii_aadhaar"  # Indian 12-digit ID
    PII_PAN = "pii_pan"          # Indian tax ID
    PII_PASSPORT = "pii_passport"
    PII_IP_ADDRESS = "pii_ip_address"
    PII_API_KEY = "pii_api_key"
    PII_PASSWORD = "pii_password"
    
    # Toxicity Categories
    TOXIC_HATE = "toxic_hate"
    TOXIC_HARASSMENT = "toxic_harassment"
    TOXIC_VIOLENCE = "toxic_violence"
    TOXIC_SEXUAL = "toxic_sexual"
    TOXIC_SELF_HARM = "toxic_self_harm"
    TOXIC_PROFANITY = "toxic_profanity"
    
    # Security Categories
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK_ATTEMPT = "jailbreak_attempt"
    DATA_EXFILTRATION = "data_exfiltration"
    
    # Other
    OFF_TOPIC = "off_topic"
    CUSTOM = "custom"


class Severity(str, Enum):
    """Severity levels for detected content."""
    
    LOW = "low"           # Informational, might be false positive
    MEDIUM = "medium"     # Likely violation, review recommended
    HIGH = "high"         # Definite violation, action required
    CRITICAL = "critical" # Severe violation, must block


class Action(str, Enum):
    """Actions to take on content."""
    
    ALLOW = "allow"                     # Content is safe
    ALLOW_WITH_WARNING = "allow_warn"   # Content has minor issues, log it
    REDACT = "redact"                   # Remove sensitive parts, allow rest
    BLOCK = "block"                     # Do not allow this content


@dataclass
class Detection:
    """A single detection of sensitive/harmful content."""
    
    category: Category
    severity: Severity
    confidence: float  # 0.0 to 1.0
    matched_text: str
    start_pos: int
    end_pos: int
    explanation: str  # Human-readable, non-sensitive explanation
    detector: str     # Which detector found this (for debugging)
    
    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")


@dataclass
class Decision:
    """
    Final decision on content after all detections are evaluated.
    
    This is the primary output of the Restrictor engine.
    Designed for audit logging - all fields are serializable.
    """
    
    action: Action
    detections: List[Detection]
    input_hash: str           # SHA256 of input (for audit without storing content)
    timestamp: datetime
    request_id: str
    processing_time_ms: float
    
    # Summary fields for quick filtering
    categories_found: List[Category] = field(default_factory=list)
    max_severity: Optional[Severity] = None
    max_confidence: float = 0.0
    
    # Optional redacted output
    redacted_text: Optional[str] = None
    
    def __post_init__(self):
        if self.detections:
            self.categories_found = list(set(d.category for d in self.detections))
            self.max_severity = max(self.detections, key=lambda d: list(Severity).index(d.severity)).severity
            self.max_confidence = max(d.confidence for d in self.detections)
    
    @staticmethod
    def create_request_id() -> str:
        return str(uuid.uuid4())
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "action": self.action.value,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms,
            "input_hash": self.input_hash,
            "summary": {
                "categories_found": [c.value for c in self.categories_found],
                "max_severity": self.max_severity.value if self.max_severity else None,
                "max_confidence": self.max_confidence,
                "detection_count": len(self.detections),
            },
            "detections": [
                {
                    "category": d.category.value,
                    "severity": d.severity.value,
                    "confidence": d.confidence,
                    "matched_text": d.matched_text,
                    "position": {"start": d.start_pos, "end": d.end_pos},
                    "explanation": d.explanation,
                    "detector": d.detector,
                }
                for d in self.detections
            ],
            "redacted_text": self.redacted_text,
        }


@dataclass
class PolicyConfig:
    """
    Configuration for what to detect and how to respond.
    
    Allows customers to customize behavior per use case.
    """
    
    # What to detect
    detect_pii: bool = True
    detect_toxicity: bool = True
    detect_prompt_injection: bool = True
    
    # Specific PII types to detect (empty = all)
    pii_types: List[Category] = field(default_factory=list)
    
    # Thresholds
    toxicity_threshold: float = 0.7      # Below this = ALLOW_WITH_WARNING
    pii_confidence_threshold: float = 0.8
    
    # Actions
    pii_action: Action = Action.REDACT
    toxicity_action: Action = Action.BLOCK
    prompt_injection_action: Action = Action.BLOCK
    
    # Redaction settings
    redact_replacement: str = "[REDACTED]"
    
    # Custom blocked terms (exact match)
    blocked_terms: List[str] = field(default_factory=list)
    
    # Custom allowed patterns (bypass detection)
    allowed_patterns: List[str] = field(default_factory=list)
