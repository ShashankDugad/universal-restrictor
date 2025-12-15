"""
Data models for Universal Restrictor.
"""

from enum import Enum
from typing import List, Optional
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


@dataclass
class PolicyConfig:
    """Configuration for detection policies."""
    toxicity_threshold: float = 0.7
    pii_action: Action = Action.REDACT
    toxicity_action: Action = Action.BLOCK
    prompt_injection_action: Action = Action.BLOCK
    blocked_terms: List[str] = field(default_factory=list)
    allowed_domains: List[str] = field(default_factory=list)
