"""
Data models for Universal Restrictor.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class Action(str, Enum):
    """Actions to take based on detection."""
    ALLOW = "allow"
    ALLOW_WITH_WARNING = "allow_with_warning"
    REDACT = "redact"
    BLOCK = "block"


class Severity(str, Enum):
    """Severity levels for detections."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Category(str, Enum):
    """Categories of detected content."""
    
    # PII Categories
    PII_NAME = "pii_name"
    PII_EMAIL = "pii_email"
    PII_PHONE = "pii_phone"
    PII_ADDRESS = "pii_address"
    PII_SSN = "pii_ssn"
    PII_CREDIT_CARD = "pii_credit_card"
    PII_AADHAAR = "pii_aadhaar"
    PII_PAN = "pii_pan"
    PII_PASSPORT = "pii_passport"
    PII_IP_ADDRESS = "pii_ip_address"
    PII_API_KEY = "pii_api_key"
    PII_PASSWORD = "pii_password"
    
    # India Finance Categories
    PII_BANK_ACCOUNT = "pii_bank_account"
    PII_IFSC = "pii_ifsc"
    PII_UPI = "pii_upi"
    PII_DEMAT = "pii_demat"
    PII_GST = "pii_gst"
    
    # Finance Intent Categories
    FINANCE_TRADING_INTENT = "finance_trading_intent"
    FINANCE_INSIDER_INFO = "finance_insider_info"
    FINANCE_INVESTMENT_ADVICE = "finance_investment_advice"
    FINANCE_LOAN_DISCUSSION = "finance_loan_discussion"
    
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
    
    # Custom category for extensibility
    CUSTOM = "custom"


@dataclass
class Detection:
    """A single detection result."""
    category: Category
    severity: Severity
    confidence: float
    matched_text: str
    start_pos: int
    end_pos: int
    explanation: str
    detector: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "matched_text": self.matched_text,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "explanation": self.explanation,
            "detector": self.detector,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Detection":
        """Create from dictionary."""
        return cls(
            category=Category(data["category"]),
            severity=Severity(data["severity"]),
            confidence=data["confidence"],
            matched_text=data["matched_text"],
            start_pos=data["start_pos"],
            end_pos=data["end_pos"],
            explanation=data["explanation"],
            detector=data["detector"],
        )


@dataclass
class Decision:
    """Final decision for a piece of text."""
    action: Action
    detections: List[Detection]
    input_hash: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    processing_time_ms: float = 0.0
    categories_found: List[Category] = field(default_factory=list)
    max_severity: Optional[Severity] = None
    max_confidence: float = 0.0
    redacted_text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action": self.action.value,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "processing_time_ms": self.processing_time_ms,
            "input_hash": self.input_hash,
            "categories_found": [c.value for c in self.categories_found],
            "max_severity": self.max_severity.value if self.max_severity else None,
            "max_confidence": self.max_confidence,
            "redacted_text": self.redacted_text,
            "detections": [d.to_dict() for d in self.detections],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Decision":
        """Create from dictionary."""
        return cls(
            action=Action(data["action"]),
            detections=[Detection.from_dict(d) for d in data.get("detections", [])],
            input_hash=data.get("input_hash", ""),
            request_id=data.get("request_id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.utcnow(),
            processing_time_ms=data.get("processing_time_ms", 0.0),
            categories_found=[Category(c) for c in data.get("categories_found", [])],
            max_severity=Severity(data["max_severity"]) if data.get("max_severity") else None,
            max_confidence=data.get("max_confidence", 0.0),
            redacted_text=data.get("redacted_text"),
        )


@dataclass
class PolicyConfig:
    """Configuration for detection policies."""
    
    # Detection toggles
    detect_pii: bool = True
    detect_toxicity: bool = True
    detect_prompt_injection: bool = True
    detect_finance_intent: bool = True
    
    # Thresholds
    toxicity_threshold: float = 0.7
    pii_confidence_threshold: float = 0.8
    prompt_injection_threshold: float = 0.8
    
    # PII configuration
    pii_types: Optional[List[str]] = None  # None = all types
    redact_replacement: str = "[REDACTED]"  # Custom replacement text
    
    # Actions per category
    pii_action: Action = Action.REDACT
    toxicity_action: Action = Action.BLOCK
    prompt_injection_action: Action = Action.BLOCK
    finance_intent_action: Action = Action.ALLOW_WITH_WARNING
    
    # Custom rules
    blocked_terms: List[str] = field(default_factory=list)
    allowed_domains: List[str] = field(default_factory=list)
    custom_patterns: Dict[str, str] = field(default_factory=dict)  # name -> regex
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "detect_pii": self.detect_pii,
            "detect_toxicity": self.detect_toxicity,
            "detect_prompt_injection": self.detect_prompt_injection,
            "detect_finance_intent": self.detect_finance_intent,
            "toxicity_threshold": self.toxicity_threshold,
            "pii_confidence_threshold": self.pii_confidence_threshold,
            "prompt_injection_threshold": self.prompt_injection_threshold,
            "pii_types": self.pii_types,
            "redact_replacement": self.redact_replacement,
            "pii_action": self.pii_action.value,
            "toxicity_action": self.toxicity_action.value,
            "prompt_injection_action": self.prompt_injection_action.value,
            "finance_intent_action": self.finance_intent_action.value,
            "blocked_terms": self.blocked_terms,
            "allowed_domains": self.allowed_domains,
            "custom_patterns": self.custom_patterns,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyConfig":
        """Create from dictionary."""
        return cls(
            detect_pii=data.get("detect_pii", True),
            detect_toxicity=data.get("detect_toxicity", True),
            detect_prompt_injection=data.get("detect_prompt_injection", True),
            detect_finance_intent=data.get("detect_finance_intent", True),
            toxicity_threshold=data.get("toxicity_threshold", 0.7),
            pii_confidence_threshold=data.get("pii_confidence_threshold", 0.8),
            prompt_injection_threshold=data.get("prompt_injection_threshold", 0.8),
            pii_types=data.get("pii_types"),
            redact_replacement=data.get("redact_replacement", "[REDACTED]"),
            pii_action=Action(data.get("pii_action", "redact")),
            toxicity_action=Action(data.get("toxicity_action", "block")),
            prompt_injection_action=Action(data.get("prompt_injection_action", "block")),
            finance_intent_action=Action(data.get("finance_intent_action", "allow_with_warning")),
            blocked_terms=data.get("blocked_terms", []),
            allowed_domains=data.get("allowed_domains", []),
            custom_patterns=data.get("custom_patterns", {}),
        )
