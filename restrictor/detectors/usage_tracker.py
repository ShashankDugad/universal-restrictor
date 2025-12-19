"""
Persistent Usage Tracker - Stores Claude API usage in Redis.
"""

import logging
import os
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)


class UsageTracker:
    """Tracks Claude API usage persistently in Redis."""

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self._client = None
        self._connect()

        # Keys
        self.total_key = "usage:claude:total"
        self.daily_key_prefix = "usage:claude:daily:"

    def _connect(self):
        """Connect to Redis."""
        if not self.redis_url:
            logger.warning("No REDIS_URL for usage tracker")
            return
        try:
            import redis
            self._client = redis.from_url(self.redis_url)
            self._client.ping()
            logger.info("Usage tracker connected to Redis")
        except Exception as e:
            logger.error(f"Usage tracker Redis connection failed: {e}")
            self._client = None

    @property
    def is_connected(self) -> bool:
        if self._client is None:
            return False
        try:
            self._client.ping()
            return True
        except Exception:
            return False

    def _get_daily_key(self) -> str:
        """Get today's daily key."""
        return f"{self.daily_key_prefix}{date.today().isoformat()}"

    def record_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        blocked: bool = False
    ):
        """Record API usage."""
        if not self.is_connected:
            return

        try:
            # Update total stats
            self._client.hincrby(self.total_key, "total_requests", 1)
            self._client.hincrby(self.total_key, "input_tokens", input_tokens)
            self._client.hincrby(self.total_key, "output_tokens", output_tokens)
            self._client.hincrbyfloat(self.total_key, "total_cost_usd", cost_usd)

            if blocked:
                self._client.hincrby(self.total_key, "blocked_requests", 1)

            # Update daily stats
            daily_key = self._get_daily_key()
            self._client.hincrby(daily_key, "requests", 1)
            self._client.hincrby(daily_key, "input_tokens", input_tokens)
            self._client.hincrby(daily_key, "output_tokens", output_tokens)
            self._client.hincrbyfloat(daily_key, "cost_usd", cost_usd)

            # Set expiry on daily key (7 days)
            self._client.expire(daily_key, 7 * 24 * 60 * 60)

        except Exception as e:
            logger.error(f"Failed to record usage: {e}")

    def record_blocked(self):
        """Record a blocked/rate-limited request."""
        if not self.is_connected:
            return
        try:
            self._client.hincrby(self.total_key, "blocked_requests", 1)
        except Exception as e:
            logger.error(f"Failed to record blocked: {e}")

    def get_usage(self, daily_cap_usd: float = 1.0) -> dict:
        """Get usage statistics."""
        default = {
            "total_requests": 0,
            "blocked_requests": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "daily_cost_usd": 0.0,
            "daily_cap_usd": daily_cap_usd,
            "remaining_daily_budget": daily_cap_usd,
            "requests_per_minute_limit": 30
        }

        if not self.is_connected:
            return default

        try:
            # Get total stats
            total = self._client.hgetall(self.total_key)

            # Get daily stats
            daily_key = self._get_daily_key()
            daily = self._client.hgetall(daily_key)

            # Parse values
            def get_int(d, k):
                v = d.get(k.encode() if isinstance(k, str) else k, b'0')
                return int(v)

            def get_float(d, k):
                v = d.get(k.encode() if isinstance(k, str) else k, b'0')
                return float(v)

            total_requests = get_int(total, 'total_requests')
            blocked_requests = get_int(total, 'blocked_requests')
            input_tokens = get_int(total, 'input_tokens')
            output_tokens = get_int(total, 'output_tokens')
            total_cost = get_float(total, 'total_cost_usd')
            daily_cost = get_float(daily, 'cost_usd')

            return {
                "total_requests": total_requests,
                "blocked_requests": blocked_requests,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "total_cost_usd": round(total_cost, 6),
                "daily_cost_usd": round(daily_cost, 6),
                "daily_cap_usd": daily_cap_usd,
                "remaining_daily_budget": round(daily_cap_usd - daily_cost, 6),
                "requests_per_minute_limit": 30
            }

        except Exception as e:
            logger.error(f"Failed to get usage: {e}")
            return default

    def reset_usage(self):
        """Reset all usage stats (admin only)."""
        if not self.is_connected:
            return False
        try:
            self._client.delete(self.total_key)
            # Delete all daily keys
            for key in self._client.scan_iter(f"{self.daily_key_prefix}*"):
                self._client.delete(key)
            logger.info("Usage stats reset")
            return True
        except Exception as e:
            logger.error(f"Failed to reset usage: {e}")
            return False


# Singleton instance
_tracker: Optional[UsageTracker] = None


def get_usage_tracker() -> UsageTracker:
    """Get or create usage tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker
