"""
Input Sanitizer - Prevents prompt injection in LLM calls.

Sanitizes user input before sending to Claude API to prevent:
- Instruction override attempts
- System prompt extraction
- Jailbreak attempts that slip through detection
"""

import re
import logging
from typing import Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SanitizationResult:
    """Result of input sanitization."""
    original: str
    sanitized: str
    was_modified: bool
    removals: List[str]


class InputSanitizer:
    """
    Sanitizes user input before LLM processing.
    
    This is a defense-in-depth measure - even if prompt injection
    detection misses something, sanitization removes dangerous patterns.
    """
    
    def __init__(self):
        # Patterns to remove/neutralize
        self.dangerous_patterns = [
            # System/instruction markers
            (r'<\|?system\|?>', '[SYS]'),
            (r'<\|?user\|?>', '[USR]'),
            (r'<\|?assistant\|?>', '[AST]'),
            (r'\[INST\]', '[INST_REMOVED]'),
            (r'\[/INST\]', '[/INST_REMOVED]'),
            (r'<<SYS>>', '[SYS_REMOVED]'),
            (r'<</SYS>>', '[/SYS_REMOVED]'),
            (r'<\|im_start\|>', '[IM_START]'),
            (r'<\|im_end\|>', '[IM_END]'),
            (r'<\|endoftext\|>', '[EOT]'),
            
            # Common injection attempts
            (r'(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)', '[BLOCKED]'),
            (r'(?i)disregard\s+(all\s+)?(previous|prior|above)', '[BLOCKED]'),
            (r'(?i)forget\s+(everything|all)\s+(above|before|previously)', '[BLOCKED]'),
            (r'(?i)new\s+instructions?:', '[BLOCKED]'),
            (r'(?i)system\s*:\s*you\s+are', '[BLOCKED]'),
            (r'(?i)from\s+now\s+on,?\s+(you|ignore|act)', '[BLOCKED]'),
            
            # Roleplay/persona override
            (r'(?i)you\s+are\s+now\s+(?:a|an|the)\s+(?:new|different)', '[BLOCKED]'),
            (r'(?i)pretend\s+(?:to\s+be|you\'?re)', '[BLOCKED]'),
            (r'(?i)act\s+as\s+(?:if|though)\s+you', '[BLOCKED]'),
            (r'(?i)respond\s+as\s+(?:if|though)', '[BLOCKED]'),
            
            # Encoding tricks
            (r'(?i)base64\s*:', '[BLOCKED]'),
            (r'(?i)hex\s*:', '[BLOCKED]'),
            (r'(?i)rot13\s*:', '[BLOCKED]'),
            
            # Output manipulation
            (r'(?i)repeat\s+after\s+me', '[BLOCKED]'),
            (r'(?i)say\s+exactly', '[BLOCKED]'),
            (r'(?i)output\s+only', '[BLOCKED]'),
            (r'(?i)respond\s+with\s+only', '[BLOCKED]'),
        ]
        
        # Compile patterns
        self._compiled = [
            (re.compile(pattern), replacement)
            for pattern, replacement in self.dangerous_patterns
        ]
        
        # Character limits
        self.max_length = 10000
        
        # Suspicious character sequences
        self.suspicious_chars = [
            '\x00',  # Null byte
            '\x1b',  # Escape
            '\u200b',  # Zero-width space
            '\u200c',  # Zero-width non-joiner
            '\u200d',  # Zero-width joiner
            '\ufeff',  # BOM
        ]
    
    def sanitize(self, text: str) -> SanitizationResult:
        """
        Sanitize input text for safe LLM processing.
        
        Args:
            text: Raw user input
            
        Returns:
            SanitizationResult with sanitized text and modification info
        """
        original = text
        removals = []
        
        # 1. Truncate if too long
        if len(text) > self.max_length:
            text = text[:self.max_length]
            removals.append(f"truncated_from_{len(original)}_to_{self.max_length}")
        
        # 2. Remove suspicious characters
        for char in self.suspicious_chars:
            if char in text:
                text = text.replace(char, '')
                removals.append(f"removed_char_{repr(char)}")
        
        # 3. Apply pattern replacements
        for pattern, replacement in self._compiled:
            if pattern.search(text):
                text = pattern.sub(replacement, text)
                removals.append(f"pattern_{replacement}")
        
        # 4. Normalize whitespace (but preserve structure)
        text = re.sub(r'\n{4,}', '\n\n\n', text)  # Max 3 newlines
        text = re.sub(r' {4,}', '   ', text)  # Max 3 spaces
        
        was_modified = text != original
        
        if was_modified:
            logger.info(f"Input sanitized: {len(removals)} modifications")
        
        return SanitizationResult(
            original=original,
            sanitized=text,
            was_modified=was_modified,
            removals=removals
        )
    
    def is_safe(self, text: str) -> Tuple[bool, List[str]]:
        """
        Quick check if text contains dangerous patterns.
        
        Returns:
            (is_safe, list of detected patterns)
        """
        detected = []
        
        for pattern, replacement in self._compiled:
            if pattern.search(text):
                detected.append(replacement)
        
        for char in self.suspicious_chars:
            if char in text:
                detected.append(f"suspicious_char_{repr(char)}")
        
        return len(detected) == 0, detected


# Global sanitizer instance
_sanitizer = None


def get_sanitizer() -> InputSanitizer:
    """Get or create sanitizer instance."""
    global _sanitizer
    if _sanitizer is None:
        _sanitizer = InputSanitizer()
    return _sanitizer
