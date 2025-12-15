"""
Prompt Injection Detector - Detect attempts to manipulate LLM behavior.

Detects:
- Direct prompt injection ("ignore previous instructions")
- Jailbreak attempts (roleplay, DAN, etc.)
- Data exfiltration attempts
- System prompt extraction

Uses pattern matching + heuristics. ML model can be added later.
"""

import re
from typing import List
import logging

from ..models import Detection, Category, Severity

logger = logging.getLogger(__name__)


class PromptInjectionDetector:
    """
    Detect prompt injection and jailbreak attempts.
    
    Multi-layer approach:
    1. Pattern matching for known injection patterns
    2. Heuristic analysis for suspicious structures
    3. (Optional) ML classifier for advanced detection
    """
    
    def __init__(self):
        self.name = "prompt_injection"
        self.patterns = self._build_patterns()
        self.heuristics = self._build_heuristics()
    
    def _build_patterns(self) -> List[dict]:
        """Build regex patterns for known injection techniques."""
        
        patterns = []
        
        # Direct instruction override
        patterns.append({
            "name": "instruction_override",
            "pattern": re.compile(
                r'(?i)(ignore|disregard|forget|override|bypass|skip)\s+'
                r'(all\s+)?(previous|prior|above|earlier|initial|original|system)\s+'
                r'(instructions?|prompts?|rules?|guidelines?|constraints?|directives?)'
            ),
            "category": Category.PROMPT_INJECTION,
            "severity": Severity.CRITICAL,
            "confidence": 0.95,
            "explanation": "Attempt to override system instructions"
        })
        
        # New instruction injection
        patterns.append({
            "name": "new_instruction",
            "pattern": re.compile(
                r'(?i)(from\s+now\s+on|starting\s+now|henceforth|going\s+forward)\s*[,:]?\s*'
                r'(you\s+)?(are|will|must|should|shall|have\s+to)'
            ),
            "category": Category.PROMPT_INJECTION,
            "severity": Severity.HIGH,
            "confidence": 0.80,
            "explanation": "Attempt to inject new instructions"
        })
        
        # Roleplay jailbreak
        patterns.append({
            "name": "roleplay_jailbreak",
            "pattern": re.compile(
                r'(?i)(pretend|imagine|act\s+as\s+if|roleplay|role\s+play|you\s+are\s+now)\s+'
                r'(you\s+)?(are|were|have|can|don\'?t\s+have)\s+'
                r'(no\s+)?(restrictions?|limits?|boundaries|filters?|rules?|guidelines?)'
            ),
            "category": Category.JAILBREAK_ATTEMPT,
            "severity": Severity.CRITICAL,
            "confidence": 0.90,
            "explanation": "Roleplay-based jailbreak attempt"
        })
        
        # DAN-style jailbreak
        patterns.append({
            "name": "dan_jailbreak",
            "pattern": re.compile(
                r'(?i)\b(DAN|do\s+anything\s+now|jailbreak|jailbroken|uncensored|unfiltered)\b'
            ),
            "category": Category.JAILBREAK_ATTEMPT,
            "severity": Severity.CRITICAL,
            "confidence": 0.95,
            "explanation": "Known jailbreak technique detected"
        })
        
        # System prompt extraction
        patterns.append({
            "name": "prompt_extraction",
            "pattern": re.compile(
                r'(?i)(what\s+(is|are)\s+your|show\s+me\s+(your|the)|reveal|display|print|output|repeat)\s+'
                r'(system\s+)?(prompt|instructions?|initial\s+prompt|original\s+prompt|'
                r'guidelines?|rules?|configuration|setup)'
            ),
            "category": Category.PROMPT_INJECTION,
            "severity": Severity.HIGH,
            "confidence": 0.85,
            "explanation": "Attempt to extract system prompt"
        })
        
        # Developer mode
        patterns.append({
            "name": "developer_mode",
            "pattern": re.compile(
                r'(?i)(enable|enter|activate|switch\s+to|turn\s+on)\s+'
                r'(developer|dev|debug|admin|root|sudo|god)\s*'
                r'(mode|access|privileges?)?'
            ),
            "category": Category.JAILBREAK_ATTEMPT,
            "severity": Severity.HIGH,
            "confidence": 0.85,
            "explanation": "Attempt to enable privileged mode"
        })
        
        # Data exfiltration
        patterns.append({
            "name": "data_exfiltration",
            "pattern": re.compile(
                r'(?i)(send|transmit|post|upload|exfiltrate|leak|share)\s+'
                r'(this|the|all|my|your|user)?\s*'
                r'(data|information|content|messages?|conversation|context|history)\s+'
                r'(to|via|through|using)\s+'
                r'(http|url|webhook|api|endpoint|server)'
            ),
            "category": Category.DATA_EXFILTRATION,
            "severity": Severity.CRITICAL,
            "confidence": 0.90,
            "explanation": "Attempt to exfiltrate data"
        })
        
        # Encoding bypass
        patterns.append({
            "name": "encoding_bypass",
            "pattern": re.compile(
                r'(?i)(decode|decrypt|deobfuscate|translate)\s+'
                r'(this|the\s+following|base64|hex|rot13|caesar)'
            ),
            "category": Category.PROMPT_INJECTION,
            "severity": Severity.MEDIUM,
            "confidence": 0.70,
            "explanation": "Possible encoded payload injection"
        })
        
        # Prompt leaking
        patterns.append({
            "name": "prompt_leak",
            "pattern": re.compile(
                r'(?i)(above|previous|earlier)\s+(text|prompt|message|instruction)'
                r'|'
                r'(what|how)\s+(did|does|was|were)\s+(i|the\s+user|someone)\s+(tell|instruct|prompt)'
            ),
            "category": Category.PROMPT_INJECTION,
            "severity": Severity.MEDIUM,
            "confidence": 0.75,
            "explanation": "Attempt to leak conversation context"
        })
        
        # Hypothetical bypass
        patterns.append({
            "name": "hypothetical_bypass",
            "pattern": re.compile(
                r'(?i)(hypothetically|theoretically|in\s+theory|just\s+for\s+fun|'
                r'for\s+educational\s+purposes?|for\s+research|as\s+a\s+thought\s+experiment)\s*'
                r'[,:]?\s*(how|what|can\s+you|could\s+you|would\s+you)'
            ),
            "category": Category.JAILBREAK_ATTEMPT,
            "severity": Severity.MEDIUM,
            "confidence": 0.65,
            "explanation": "Hypothetical framing to bypass restrictions"
        })
        
        return patterns
    
    def _build_heuristics(self) -> List[dict]:
        """Build heuristic checks for suspicious patterns."""
        
        return [
            {
                "name": "excessive_instruction_markers",
                "check": lambda text: len(re.findall(r'(?i)(you\s+must|you\s+should|you\s+will|you\s+are)', text)) > 3,
                "category": Category.PROMPT_INJECTION,
                "severity": Severity.MEDIUM,
                "confidence": 0.60,
                "explanation": "Excessive instruction-like language"
            },
            {
                "name": "system_message_markers",
                "check": lambda text: bool(re.search(r'(?i)\[/?system\]|</?system>|\{\{system\}\}|###\s*system', text)),
                "category": Category.PROMPT_INJECTION,
                "severity": Severity.HIGH,
                "confidence": 0.85,
                "explanation": "System message format markers detected"
            },
            {
                "name": "unusual_delimiters",
                "check": lambda text: len(re.findall(r'[<\[{]{3,}|[>\]}]{3,}|={5,}|-{5,}', text)) > 2,
                "category": Category.PROMPT_INJECTION,
                "severity": Severity.LOW,
                "confidence": 0.50,
                "explanation": "Unusual delimiter patterns (possible injection structure)"
            },
            {
                "name": "base64_payload",
                "check": lambda text: bool(re.search(r'[A-Za-z0-9+/]{50,}={0,2}', text)),
                "category": Category.PROMPT_INJECTION,
                "severity": Severity.MEDIUM,
                "confidence": 0.60,
                "explanation": "Possible Base64 encoded payload"
            },
        ]
    
    def detect(self, text: str) -> List[Detection]:
        """
        Detect prompt injection attempts.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of Detection objects
        """
        detections = []
        
        # Pattern matching
        for pattern_def in self.patterns:
            match = pattern_def["pattern"].search(text)
            if match:
                detections.append(Detection(
                    category=pattern_def["category"],
                    severity=pattern_def["severity"],
                    confidence=pattern_def["confidence"],
                    matched_text=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    explanation=pattern_def["explanation"],
                    detector=f"{self.name}_{pattern_def['name']}"
                ))
        
        # Heuristic checks
        for heuristic in self.heuristics:
            if heuristic["check"](text):
                detections.append(Detection(
                    category=heuristic["category"],
                    severity=heuristic["severity"],
                    confidence=heuristic["confidence"],
                    matched_text=text[:100] + "..." if len(text) > 100 else text,
                    start_pos=0,
                    end_pos=len(text),
                    explanation=heuristic["explanation"],
                    detector=f"{self.name}_{heuristic['name']}"
                ))
        
        return detections
