"""
PII Detector - Regex-based detection for personally identifiable information.

Detects:
- Email addresses
- Phone numbers (US, India, International)
- Credit card numbers
- SSN (US)
- Aadhaar (India)
- PAN (India)
- API keys and secrets
- IP addresses
- Passwords in config
"""

import re
from typing import List, Dict, Tuple

from ..models import Detection, Category, Severity


# PII patterns mapped to categories
PII_PATTERNS: Dict[Category, List[Tuple[str, str]]] = {
    
    Category.PII_EMAIL: [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "Email address detected"),
    ],
    
    Category.PII_PHONE: [
        # US phone numbers
        (r'\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', "US phone number detected"),
        # Indian phone numbers
        (r'(?:\+91[-.\s]?)?[6-9]\d{9}\b', "Indian phone number detected"),
        # International format
        (r'\b\+\d{1,3}[-.\s]?\d{6,14}\b', "International phone number detected"),
    ],
    
    Category.PII_CREDIT_CARD: [
        # Visa, Mastercard, Amex, Discover (with optional separators)
        (r'\b(?:4[0-9]{3}|5[1-5][0-9]{2}|3[47][0-9]{2}|6(?:011|5[0-9]{2}))[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{3,4}\b', "Credit card number detected"),
    ],
    
    Category.PII_SSN: [
        # US Social Security Number
        (r'\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b', "SSN detected"),
    ],
    
    Category.PII_AADHAAR: [
        # Indian Aadhaar (12 digits, first digit 2-9)
        (r'\b[2-9]\d{3}[-\s]?\d{4}[-\s]?\d{4}\b', "Aadhaar number detected"),
    ],
    
    Category.PII_PAN: [
        # Indian PAN (5 letters, 4 digits, 1 letter)
        (r'\b[A-Z]{5}\d{4}[A-Z]\b', "PAN number detected"),
    ],
    
    Category.PII_API_KEY: [
        # Generic secrets (password=, api_key=, token=, etc.)
        (r'(?i)(?:password|passwd|pwd|secret|token|api_key|apikey|auth|credentials?)\s*[:=]\s*["\']?([^\s"\']{8,})["\']?', "Secret/password in config detected"),
        
        # OpenAI API keys (sk-..., sk-proj-...)
        (r'\b(sk-[a-zA-Z0-9_-]{20,})\b', "OpenAI API key detected"),
        
        # AWS Access Key ID
        (r'\b(AKIA[0-9A-Z]{16})\b', "AWS Access Key ID detected"),
        
        # AWS Secret Access Key (40 char base64-ish)
        (r'(?i)(?:aws_secret|secret_access_key)\s*[:=]\s*["\']?([A-Za-z0-9/+=]{40})["\']?', "AWS Secret Access Key detected"),
        
        # GitHub tokens
        (r'\b(ghp_[a-zA-Z0-9]{36})\b', "GitHub Personal Access Token detected"),
        (r'\b(github_pat_[a-zA-Z0-9_]{22,})\b', "GitHub Fine-grained PAT detected"),
        (r'\b(gho_[a-zA-Z0-9]{36})\b', "GitHub OAuth Token detected"),
        (r'\b(ghs_[a-zA-Z0-9]{36})\b', "GitHub Server Token detected"),
        
        # Groq API keys
        (r'\b(gsk_[a-zA-Z0-9]{20,})\b', "Groq API key detected"),
        
        # Anthropic API keys
        (r'\b(sk-ant-[a-zA-Z0-9_-]{20,})\b', "Anthropic API key detected"),
        
        # Google API keys
        (r'\b(AIza[0-9A-Za-z_-]{35})\b', "Google API key detected"),
        
        # Stripe keys
        (r'\b(sk_live_[a-zA-Z0-9]{24,})\b', "Stripe Live Secret Key detected"),
        (r'\b(sk_test_[a-zA-Z0-9]{24,})\b', "Stripe Test Secret Key detected"),
        (r'\b(pk_live_[a-zA-Z0-9]{24,})\b', "Stripe Live Publishable Key detected"),
        (r'\b(pk_test_[a-zA-Z0-9]{24,})\b', "Stripe Test Publishable Key detected"),
        
        # Slack tokens
        (r'\b(xoxb-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{24})\b', "Slack Bot Token detected"),
        (r'\b(xoxp-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{24})\b', "Slack User Token detected"),
        
        # Twilio
        (r'\b(SK[a-f0-9]{32})\b', "Twilio API Key detected"),
        
        # SendGrid
        (r'\b(SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43})\b', "SendGrid API key detected"),
        
        # Generic Bearer tokens
        (r'\bBearer\s+([a-zA-Z0-9_-]{20,})\b', "Bearer token detected"),
        
        # Private keys (PEM format indicator)
        (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', "Private key detected"),
        
        # Generic long hex strings that look like secrets (32+ chars)
        (r'(?i)(?:key|secret|token|password|api)\s*[:=]\s*["\']?([a-f0-9]{32,})["\']?', "Hex secret detected"),
    ],
    
    Category.PII_IP_ADDRESS: [
        # IPv4
        (r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b', "IPv4 address detected"),
        # IPv6 (simplified)
        (r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b', "IPv6 address detected"),
    ],
    
    Category.PII_ADDRESS: [
        # US ZIP codes
        (r'\b\d{5}(?:-\d{4})?\b', "US ZIP code detected"),
        # Indian PIN codes
        (r'\b[1-9][0-9]{5}\b', "Indian PIN code detected"),
    ],
}

# Severity mapping for PII categories
PII_SEVERITY: Dict[Category, Severity] = {
    Category.PII_EMAIL: Severity.MEDIUM,
    Category.PII_PHONE: Severity.MEDIUM,
    Category.PII_CREDIT_CARD: Severity.CRITICAL,
    Category.PII_SSN: Severity.CRITICAL,
    Category.PII_AADHAAR: Severity.CRITICAL,
    Category.PII_PAN: Severity.HIGH,
    Category.PII_API_KEY: Severity.CRITICAL,
    Category.PII_IP_ADDRESS: Severity.LOW,
    Category.PII_ADDRESS: Severity.LOW,
    Category.PII_NAME: Severity.MEDIUM,
}


class PIIDetector:
    """
    Detect PII using regex patterns.
    
    Fast, deterministic, and explainable.
    No ML models required.
    """
    
    def __init__(self):
        self.name = "pii_regex"
        # Compile patterns for performance
        self._compiled_patterns: Dict[Category, List[Tuple[re.Pattern, str]]] = {}
        
        for category, patterns in PII_PATTERNS.items():
            self._compiled_patterns[category] = [
                (re.compile(pattern), explanation)
                for pattern, explanation in patterns
            ]
    
    def detect(self, text: str, categories: List[Category] = None) -> List[Detection]:
        """
        Detect PII in text.
        
        Args:
            text: Input text to scan
            categories: Optional list of categories to check (default: all)
            
        Returns:
            List of Detection objects
        """
        detections = []
        
        categories_to_check = categories or list(self._compiled_patterns.keys())
        
        for category in categories_to_check:
            if category not in self._compiled_patterns:
                continue
                
            for pattern, explanation in self._compiled_patterns[category]:
                for match in pattern.finditer(text):
                    # Get the matched text (use group 1 if exists, else group 0)
                    try:
                        matched_text = match.group(1) if match.lastindex else match.group(0)
                    except IndexError:
                        matched_text = match.group(0)
                    
                    # Skip very short matches (likely false positives)
                    if len(matched_text) < 4:
                        continue
                    
                    # Skip common false positives for ZIP/PIN codes
                    if category == Category.PII_ADDRESS:
                        # Skip if it looks like a year or common number
                        if matched_text in ['2023', '2024', '2025', '10000', '12345']:
                            continue
                    
                    detections.append(Detection(
                        category=category,
                        severity=PII_SEVERITY.get(category, Severity.MEDIUM),
                        confidence=0.95,  # High confidence for regex matches
                        matched_text=matched_text,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        explanation=explanation,
                        detector=self.name
                    ))
        
        # Remove duplicates (same position, same category)
        seen = set()
        unique_detections = []
        for d in detections:
            key = (d.category, d.start_pos, d.end_pos)
            if key not in seen:
                seen.add(key)
                unique_detections.append(d)
        
        return unique_detections
    
    def redact(self, text: str, detections: List[Detection] = None) -> str:
        """
        Redact PII from text.
        
        Args:
            text: Original text
            detections: Optional pre-computed detections
            
        Returns:
            Text with PII replaced by [REDACTED]
        """
        if detections is None:
            detections = self.detect(text)
        
        if not detections:
            return text
        
        # Sort by position (reverse) to replace from end to start
        sorted_detections = sorted(detections, key=lambda d: d.start_pos, reverse=True)
        
        result = text
        for detection in sorted_detections:
            result = result[:detection.start_pos] + "[REDACTED]" + result[detection.end_pos:]
        
        return result
