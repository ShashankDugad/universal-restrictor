"""
Universal Restrictor - Model-agnostic content classification for LLM applications.

Detects PII, toxic content, and prompt injection attempts.
Returns auditable decisions: ALLOW, ALLOW_WITH_WARNING, BLOCK
"""

__version__ = "0.1.0"

from .engine import Restrictor
from .models import Action, Category, Decision, PolicyConfig, Severity

__all__ = ["Restrictor", "Decision", "Category", "Severity", "Action", "PolicyConfig"]
