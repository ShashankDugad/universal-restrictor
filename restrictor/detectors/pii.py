"""
PII Detector - Regex-based detection for personally identifiable information.
"""

import re
from typing import List, Dict, Tuple, Set, Optional

from ..models import Detection, Category, Severity


PII_PATTERNS: Dict[Category, List[Tuple[str, str]]] = {
    
    Category.PII_EMAIL: [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "Email address detected"),
    ],
    
    Category.PII_PHONE: [
        (r'\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', "US phone number detected"),
        (r'(?<!\d)(?:\+91[-.\s]?)?[6-9]\d{9}(?![@\d])', "Indian phone number detected"),
    ],
    
    Category.PII_CREDIT_CARD: [
        (r'\b(?:4[0-9]{3}|5[1-5][0-9]{2}|3[47][0-9]{2}|6(?:011|5[0-9]{2}))[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{3,4}\b', "Credit card number detected"),
    ],
    
    Category.PII_SSN: [
        (r'\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b', "SSN detected"),
    ],
    
    Category.PII_AADHAAR: [
        (r'\b[2-9]\d{3}[-\s]?\d{4}[-\s]?\d{4}\b', "Aadhaar number detected"),
    ],
    
    Category.PII_PAN: [
        (r'\b[A-Z]{5}\d{4}[A-Z]\b', "PAN number detected"),
    ],
    
    # India Finance
    Category.PII_BANK_ACCOUNT: [
        (r'(?i)(?:account|a/c|ac|acct)[-.\s]*(?:no|number|#)?[-.\s:]*(\d{9,18})', "Bank account number detected"),
        (r'\b(\d{11,18})\b', "Potential bank account number detected"),
    ],
    
    Category.PII_IFSC: [
        (r'\b([A-Z]{4}0[A-Z0-9]{6})\b', "IFSC code detected"),
    ],
    
    Category.PII_UPI: [
        (r'([a-zA-Z0-9._-]+@(?:okaxis|okhdfcbank|okicici|oksbi|ybl|paytm|apl|yapl|ibl|axl|upi|pingpay|abfspay|freecharge|ikwik|myicici|imobile|sbi|hdfcbank|icici|axisbank|kotak|indus|federal|rbl|yesbank|idbi|citi|hsbc|sc|dbs|jupiter|fi|slice|groww))', "UPI ID detected"),
    ],
    
    Category.PII_DEMAT: [
        (r'\b(IN\d{14})\b', "CDSL Demat account detected"),
        (r'\b(IN[A-Z0-9]{6}\d{8})\b', "NSDL Demat account detected"),
    ],
    
    Category.PII_GST: [
        (r'\b(\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z])\b', "GST number detected"),
    ],
    
    # API Keys
    Category.PII_API_KEY: [
        (r'(?i)(?:password|passwd|pwd|secret|token|api_key|apikey)\s*[:=]\s*["\']?([^\s"\']{8,})["\']?', "Secret detected"),
        (r'\b(sk-[a-zA-Z0-9_-]{20,})\b', "OpenAI API key detected"),
        (r'\b(AKIA[0-9A-Z]{16})\b', "AWS Access Key detected"),
        (r'\b(ghp_[a-zA-Z0-9]{36})\b', "GitHub token detected"),
        (r'\b(gsk_[a-zA-Z0-9]{20,})\b', "Groq API key detected"),
        (r'\b(rzp_(?:live|test)_[a-zA-Z0-9]{14,})\b', "Razorpay key detected"),
    ],
    
    Category.PII_IP_ADDRESS: [
        (r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b', "IPv4 address detected"),
    ],
}

PII_SEVERITY: Dict[Category, Severity] = {
    Category.PII_EMAIL: Severity.MEDIUM,
    Category.PII_PHONE: Severity.MEDIUM,
    Category.PII_CREDIT_CARD: Severity.CRITICAL,
    Category.PII_SSN: Severity.CRITICAL,
    Category.PII_AADHAAR: Severity.CRITICAL,
    Category.PII_PAN: Severity.HIGH,
    Category.PII_API_KEY: Severity.CRITICAL,
    Category.PII_IP_ADDRESS: Severity.LOW,
    Category.PII_BANK_ACCOUNT: Severity.CRITICAL,
    Category.PII_IFSC: Severity.MEDIUM,
    Category.PII_UPI: Severity.HIGH,
    Category.PII_DEMAT: Severity.CRITICAL,
    Category.PII_GST: Severity.HIGH,
}


class PIIDetector:
    """Detect PII using regex patterns."""
    
    def __init__(self):
        self.name = "pii_regex"
        self._compiled_patterns: Dict[Category, List[Tuple[re.Pattern, str]]] = {}
        
        for category, patterns in PII_PATTERNS.items():
            self._compiled_patterns[category] = [
                (re.compile(pattern), explanation)
                for pattern, explanation in patterns
            ]
    
    def detect(self, text: str, categories: List[Category] = None) -> List[Detection]:
        """Detect PII in text."""
        detections = []
        categories_to_check = categories or list(self._compiled_patterns.keys())
        
        # Find UPI positions first to avoid phone false positives
        upi_positions: Set[Tuple[int, int]] = set()
        if Category.PII_UPI in self._compiled_patterns:
            for pattern, _ in self._compiled_patterns[Category.PII_UPI]:
                for match in pattern.finditer(text):
                    upi_positions.add((match.start(), match.end()))
        
        for category in categories_to_check:
            if category not in self._compiled_patterns:
                continue
                
            for pattern, explanation in self._compiled_patterns[category]:
                for match in pattern.finditer(text):
                    try:
                        matched_text = match.group(1) if match.lastindex else match.group(0)
                    except IndexError:
                        matched_text = match.group(0)
                    
                    if len(matched_text) < 4:
                        continue
                    
                    # Skip phone if part of UPI
                    if category == Category.PII_PHONE:
                        is_upi = any(
                            match.start() >= upi_start and match.end() <= upi_end
                            for upi_start, upi_end in upi_positions
                        )
                        if is_upi:
                            continue
                    
                    # Skip phone-like bank accounts
                    if category == Category.PII_BANK_ACCOUNT:
                        if len(matched_text) == 10 and matched_text[0] in '6789':
                            continue
                    
                    detections.append(Detection(
                        category=category,
                        severity=PII_SEVERITY.get(category, Severity.MEDIUM),
                        confidence=0.95,
                        matched_text=matched_text,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        explanation=explanation,
                        detector=self.name
                    ))
        
        # Deduplicate
        seen = set()
        unique = []
        for d in detections:
            key = (d.category, d.matched_text)
            if key not in seen:
                seen.add(key)
                unique.append(d)
        
        return unique
    
    def redact(
        self, 
        text: str, 
        detections: List[Detection] = None,
        replacement: str = "[REDACTED]"
    ) -> str:
        """
        Redact PII from text.
        
        Args:
            text: Original text
            detections: Pre-computed detections (optional)
            replacement: Replacement string (default: [REDACTED])
        """
        if detections is None:
            detections = self.detect(text)
        
        if not detections:
            return text
        
        # Sort by position (reverse) to replace from end to start
        sorted_detections = sorted(detections, key=lambda d: d.start_pos, reverse=True)
        
        result = text
        for d in sorted_detections:
            result = result[:d.start_pos] + replacement + result[d.end_pos:]
        
        return result
