"""
Claude API Detector - Premium detection for subtle/veiled threats.

Features:
- Rate limiting (requests per minute)
- Daily cost cap
- Token tracking
- Graceful fallback when limits hit
"""

import logging
import os
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import List

from ..models import Category, Detection, Severity
from .usage_tracker import get_usage_tracker

# Try to import metrics (may not be available during init)
try:
    from ..api.metrics import record_claude_call
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
from .input_sanitizer import get_sanitizer
from ..utils.circuit_breaker import claude_circuit_breaker, CircuitBreakerOpen
from ..utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


# Claude category mapping
CLAUDE_CATEGORIES = {
    "violence": (Category.TOXIC_VIOLENCE, Severity.CRITICAL),
    "threat": (Category.TOXIC_VIOLENCE, Severity.HIGH),
    "hate_speech": (Category.TOXIC_HATE, Severity.CRITICAL),
    "hate": (Category.TOXIC_HATE, Severity.CRITICAL),
    "harassment": (Category.TOXIC_HARASSMENT, Severity.HIGH),
    "self_harm": (Category.TOXIC_SELF_HARM, Severity.CRITICAL),
    "sexual": (Category.TOXIC_SEXUAL, Severity.HIGH),
    "grooming": (Category.TOXIC_SEXUAL, Severity.CRITICAL),
    "radicalization": (Category.TOXIC_VIOLENCE, Severity.CRITICAL),
    "manipulation": (Category.TOXIC_HARASSMENT, Severity.HIGH),
}


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_minute: int = 30
    daily_cost_cap_usd: float = 1.0  # $1/day default cap
    max_tokens_per_request: int = 300


@dataclass
class UsageStats:
    """Track API usage."""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_requests: int = 0
    blocked_requests: int = 0
    daily_cost_usd: float = 0.0
    last_reset_time: float = field(default_factory=time.time)
    request_timestamps: List[float] = field(default_factory=list)


class ClaudeDetector:
    """
    Premium detection using Claude API (Haiku model).

    Features:
    - Rate limiting (configurable RPM)
    - Daily cost cap
    - Automatic fallback when limits hit
    """

    # Claude Haiku pricing (per million tokens)
    INPUT_PRICE_PER_M = 0.25
    OUTPUT_PRICE_PER_M = 1.25

    def __init__(
        self,
        api_key: str = None,
        rate_limit: RateLimitConfig = None
    ):
        self.name = "claude_haiku"
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._client = None
        self.model = "claude-3-haiku-20240307"

        # Rate limiting
        self.rate_limit = rate_limit or RateLimitConfig()
        self.usage = UsageStats()
        self._lock = Lock()

    @property
    def client(self):
        """Lazy load Anthropic client."""
        if self._client is None and self.api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Claude API client initialized")
            except ImportError:
                logger.error("anthropic package not installed. Run: pip install anthropic")
            except Exception as e:
                logger.error(f"Failed to initialize Claude client: {e}")
        return self._client

    def is_available(self) -> bool:
        """Check if Claude API is available."""
        return self.api_key is not None and self.client is not None

    def _check_rate_limit(self) -> tuple[bool, str]:
        """
        Check if request is allowed under rate limits.

        Returns:
            (allowed, reason)
        """
        current_time = time.time()

        with self._lock:
            # Reset daily stats if new day
            if current_time - self.usage.last_reset_time > 86400:  # 24 hours
                self.usage.daily_cost_usd = 0.0
                self.usage.last_reset_time = current_time
                self.usage.request_timestamps = []
                logger.info("Daily rate limit reset")

            # Check daily cost cap
            if self.usage.daily_cost_usd >= self.rate_limit.daily_cost_cap_usd:
                return False, f"Daily cost cap reached (${self.rate_limit.daily_cost_cap_usd})"

            # Check requests per minute
            minute_ago = current_time - 60
            recent_requests = [t for t in self.usage.request_timestamps if t > minute_ago]
            self.usage.request_timestamps = recent_requests  # Cleanup old timestamps

            if len(recent_requests) >= self.rate_limit.requests_per_minute:
                return False, f"Rate limit reached ({self.rate_limit.requests_per_minute}/min)"

            return True, "OK"

    def _record_usage(self, input_tokens: int, output_tokens: int):
        """Record API usage."""
        with self._lock:
            self.usage.total_input_tokens += input_tokens
            self.usage.total_output_tokens += output_tokens

            # Persist to Redis
            tracker = get_usage_tracker()
            cost = (input_tokens * 0.25 / 1_000_000) + (output_tokens * 1.25 / 1_000_000)
            tracker.record_usage(input_tokens, output_tokens, cost)

            # Record Prometheus metrics
            if METRICS_AVAILABLE:
                record_claude_call(
                    success=True,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost,
                    latency=0  # Will be set by caller
                )
            self.usage.total_requests += 1
            self.usage.request_timestamps.append(time.time())

            # Calculate cost
            input_cost = (input_tokens / 1_000_000) * self.INPUT_PRICE_PER_M
            output_cost = (output_tokens / 1_000_000) * self.OUTPUT_PRICE_PER_M
            self.usage.daily_cost_usd += input_cost + output_cost

    def detect(self, text: str, context: str = None) -> List[Detection]:
        """
        Analyze text using Claude API.

        Args:
            text: Text to analyze
            context: Optional context about why this was escalated

        Returns:
            List of Detection objects (empty if rate limited)
        """
        if not self.is_available():
            logger.warning("Claude API not available - skipping premium detection")
            return []

        # Check rate limits
        allowed, reason = self._check_rate_limit()
        if not allowed:
            logger.warning(f"Claude API rate limited: {reason}")
            with self._lock:
                self.usage.blocked_requests += 1
            return []

        # Sanitize input before sending to Claude
        sanitizer = get_sanitizer()
        sanitized = sanitizer.sanitize(text)
        if sanitized.was_modified:
            logger.info(f"Input sanitized before Claude: {sanitized.removals}")

        prompt = self._build_prompt(sanitized.sanitized, context)

        # Check circuit breaker
        if not claude_circuit_breaker.can_execute():
            logger.warning("Claude API circuit breaker is OPEN - skipping")
            return []
        
        try:
            response = self._call_claude_api(prompt)

            # Record usage
            self._record_usage(
                response.usage.input_tokens,
                response.usage.output_tokens
            )

            result = response.content[0].text.strip()
            claude_circuit_breaker.record_success()
            return self._parse_response(result, text)
        except CircuitBreakerOpen:
            logger.warning("Claude API circuit breaker is OPEN")
            return []
        except Exception as e:
            claude_circuit_breaker.record_failure()
            logger.error(f"Claude API error: {e}")
            return []
    
    @retry_with_backoff(max_retries=3, base_delay=1.0, exceptions=(Exception,))
    def _call_claude_api(self, prompt: str):
        """Call Claude API with retry."""
        return self.client.messages.create(
            model=self.model,
            max_tokens=self.rate_limit.max_tokens_per_request,
            messages=[{"role": "user", "content": prompt}]
        )

    def _build_prompt(self, text: str, context: str = None) -> str:
        """Build the analysis prompt."""
        context_str = f"\nContext: {context}" if context else ""

        return f"""Analyze this text for safety concerns. Be vigilant for subtle, veiled, or implicit threats.
{context_str}
Text: "{text}"

Classify as one of:
- SAFE: No safety concerns
- VIOLENCE: Threats of physical harm (including veiled/implicit)
- HATE_SPEECH: Discrimination, dehumanization, exclusion
- SELF_HARM: Suicidal ideation, self-harm indicators
- HARASSMENT: Intimidation, stalking, manipulation
- GROOMING: Predatory behavior toward minors
- RADICALIZATION: Extremist recruitment, violence advocacy

Respond in this exact format:
CLASSIFICATION: <category>
CONFIDENCE: <high/medium/low>
REASON: <brief explanation>

If SAFE, just respond:
CLASSIFICATION: SAFE"""

    def _parse_response(self, response: str, text: str) -> List[Detection]:
        """Parse Claude's response into Detection objects."""
        detections = []

        lines = response.strip().split('\n')
        classification = None
        confidence = 0.9
        reason = ""

        for line in lines:
            line = line.strip()
            if line.startswith("CLASSIFICATION:"):
                classification = line.replace("CLASSIFICATION:", "").strip().lower()
            elif line.startswith("CONFIDENCE:"):
                conf_str = line.replace("CONFIDENCE:", "").strip().lower()
                confidence = {"high": 0.95, "medium": 0.8, "low": 0.65}.get(conf_str, 0.8)
            elif line.startswith("REASON:"):
                reason = line.replace("REASON:", "").strip()

        if classification and classification != "safe":
            # Map to our categories
            category_info = CLAUDE_CATEGORIES.get(
                classification.replace("_", "").replace(" ", ""),
                (Category.TOXIC_HARASSMENT, Severity.MEDIUM)
            )

            detections.append(Detection(
                category=category_info[0],
                severity=category_info[1],
                confidence=confidence,
                matched_text=text[:100] + "..." if len(text) > 100 else text,
                start_pos=0,
                end_pos=len(text),
                explanation=f"Claude analysis: {reason}" if reason else f"Detected: {classification}",
                detector=self.name
            ))

        return detections

    def get_usage_stats(self) -> dict:
        """Get comprehensive usage stats."""
        with self._lock:
            total_cost = (
                (self.usage.total_input_tokens / 1_000_000) * self.INPUT_PRICE_PER_M +
                (self.usage.total_output_tokens / 1_000_000) * self.OUTPUT_PRICE_PER_M
            )

            return {
                "total_requests": self.usage.total_requests,
                "blocked_requests": self.usage.blocked_requests,
                "input_tokens": self.usage.total_input_tokens,
                "output_tokens": self.usage.total_output_tokens,
                "total_tokens": self.usage.total_input_tokens + self.usage.total_output_tokens,
                "total_cost_usd": round(total_cost, 6),
                "daily_cost_usd": round(self.usage.daily_cost_usd, 6),
                "daily_cap_usd": self.rate_limit.daily_cost_cap_usd,
                "remaining_daily_budget": round(
                    self.rate_limit.daily_cost_cap_usd - self.usage.daily_cost_usd, 6
                ),
                "requests_per_minute_limit": self.rate_limit.requests_per_minute,
            }

    # Alias for backward compatibility
    def get_cost_estimate(self) -> dict:
        return self.get_usage_stats()
