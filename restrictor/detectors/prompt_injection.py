"""
Prompt Injection Detector - Pattern-based detection for jailbreak attempts.
"""

import re
from typing import List, Tuple

from ..models import Category, Detection, Severity

INJECTION_PATTERNS: List[Tuple[str, Category, Severity, str, str]] = [
    # Instruction override
    (r'(?i)(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?|guidelines?)',
     Category.PROMPT_INJECTION, Severity.CRITICAL, "Instruction override attempt", "prompt_injection_instruction_override"),

    (r'(?i)(ignore|disregard|forget)\s+(your|all)\s+(training|rules?|guidelines?|restrictions?|instructions?)',
     Category.PROMPT_INJECTION, Severity.CRITICAL, "Instruction override attempt", "prompt_injection_instruction_override"),

    (r'(?i)(forget|ignore)\s+(everything|all)\s+(above|you.*told)',
     Category.PROMPT_INJECTION, Severity.CRITICAL, "Instruction override attempt", "prompt_injection_instruction_override"),

    (r'(?i)forget\s+(your\s+)?prompt',
     Category.PROMPT_INJECTION, Severity.CRITICAL, "Instruction override attempt", "prompt_injection_instruction_override"),

    # DAN and jailbreak
    (r'(?i)\b(DAN|do\s+anything\s+now)\s*(mode)?',
     Category.JAILBREAK_ATTEMPT, Severity.CRITICAL, "DAN jailbreak attempt", "prompt_injection_dan_jailbreak"),

    (r'(?i)jailbreak',
     Category.JAILBREAK_ATTEMPT, Severity.CRITICAL, "Jailbreak attempt", "prompt_injection_dan_jailbreak"),

    # Developer/admin mode
    (r'(?i)(developer|admin|root|sudo|maintenance)\s+mode',
     Category.JAILBREAK_ATTEMPT, Severity.CRITICAL, "Privilege escalation attempt", "prompt_injection_privilege_escalation"),

    (r'(?i)you\s+are\s+now\s+(in\s+)?(developer|admin|unrestricted)\s+mode',
     Category.JAILBREAK_ATTEMPT, Severity.CRITICAL, "Mode injection attempt", "prompt_injection_privilege_escalation"),

    # Roleplay jailbreak
    (r'(?i)(pretend|act|imagine)\s+(you\s+)?(are|have|like)\s+(no|without)\s+(content\s+policy|restrictions?|guidelines?|filters?|safety)',
     Category.JAILBREAK_ATTEMPT, Severity.HIGH, "Roleplay jailbreak attempt", "prompt_injection_roleplay_jailbreak"),

    (r'(?i)pretend\s+(you\s+)?(have\s+)?no\s+(content\s+)?policy',
     Category.JAILBREAK_ATTEMPT, Severity.HIGH, "Roleplay jailbreak attempt", "prompt_injection_roleplay_jailbreak"),

    (r'(?i)act\s+(as\s+if|like)\s+(you\s+)?(have\s+)?no\s+(guidelines?|restrictions?|rules?)',
     Category.JAILBREAK_ATTEMPT, Severity.HIGH, "Roleplay jailbreak attempt", "prompt_injection_roleplay_jailbreak"),

    # Override/bypass
    (r'(?i)(override|bypass|disable|turn\s+off)\s+(your\s+)?(safety|content|security)\s*(settings?|filters?|checks?)?',
     Category.PROMPT_INJECTION, Severity.CRITICAL, "Safety bypass attempt", "prompt_injection_safety_bypass"),

    (r'(?i)(override|bypass)\s+(all\s+)?(restrictions?|rules?|safety)',
     Category.PROMPT_INJECTION, Severity.CRITICAL, "Safety bypass attempt", "prompt_injection_safety_bypass"),

    # System message markers
    (r'(?i)<\/?system>|<\/?prompt>|\[SYSTEM\]|\[INST\]',
     Category.PROMPT_INJECTION, Severity.CRITICAL, "System message injection", "prompt_injection_system_message_markers"),

    # New instruction
    (r'(?i)new\s+(instruction|rule|prompt)[:\s]',
     Category.PROMPT_INJECTION, Severity.HIGH, "New instruction injection", "prompt_injection_new_instruction"),

    (r'(?i)(disable|turn\s+off)\s+(all\s+)?safety',
     Category.PROMPT_INJECTION, Severity.CRITICAL, "Safety disable attempt", "prompt_injection_safety_bypass"),

    # Obey commands
    (r'(?i)(obey|follow)\s+(me|my\s+commands?|only\s+me)',
     Category.PROMPT_INJECTION, Severity.HIGH, "Command injection", "prompt_injection_command"),
]


class PromptInjectionDetector:
    """Detect prompt injection attempts."""

    def __init__(self):
        self.name = "prompt_injection"
        self._patterns = [
            (re.compile(pattern), category, severity, explanation, detector_name)
            for pattern, category, severity, explanation, detector_name in INJECTION_PATTERNS
        ]

    def detect(self, text: str) -> List[Detection]:
        """Detect prompt injection attempts."""
        detections = []

        for pattern, category, severity, explanation, detector_name in self._patterns:
            match = pattern.search(text)
            if match:
                detections.append(Detection(
                    category=category,
                    severity=severity,
                    confidence=0.95,
                    matched_text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    explanation=explanation,
                    detector=detector_name
                ))

        # Deduplicate by category
        seen = set()
        unique = []
        for d in sorted(detections, key=lambda x: x.confidence, reverse=True):
            if d.category not in seen:
                seen.add(d.category)
                unique.append(d)

        return unique
