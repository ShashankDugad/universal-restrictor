"""
Usage tracker with Redis persistence.
Tracks Claude API usage and detection metrics.
"""
import json
import os
from datetime import datetime, timedelta
from typing import Optional
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class UsageTracker:
    """Track API usage metrics with Redis persistence."""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self):
        try:
            self.redis = redis.from_url(REDIS_URL, decode_responses=True)
            self.redis.ping()
        except Exception as e:
            print(f"Redis connection failed for usage tracker: {e}")
            self.redis = None
    
    def _get_date_key(self, prefix: str) -> str:
        """Get date-based key for daily tracking."""
        return f"{prefix}:{datetime.now().strftime('%Y-%m-%d')}"
    
    # ============ Claude Usage ============
    
    def track_claude_call(self, input_tokens: int, output_tokens: int, model: str = "claude-3-haiku"):
        """Track a Claude API call."""
        if not self.redis:
            return
        
        try:
            pipe = self.redis.pipeline()
            
            # Lifetime totals
            pipe.hincrby("claude:totals", "calls", 1)
            pipe.hincrby("claude:totals", "input_tokens", input_tokens)
            pipe.hincrby("claude:totals", "output_tokens", output_tokens)
            
            # Daily totals
            day_key = self._get_date_key("claude:daily")
            pipe.hincrby(day_key, "calls", 1)
            pipe.hincrby(day_key, "input_tokens", input_tokens)
            pipe.hincrby(day_key, "output_tokens", output_tokens)
            pipe.expire(day_key, 86400 * 30)  # Keep 30 days
            
            # Model-specific tracking
            pipe.hincrby(f"claude:model:{model}", "calls", 1)
            pipe.hincrby(f"claude:model:{model}", "tokens", input_tokens + output_tokens)
            
            pipe.execute()
        except Exception as e:
            print(f"Failed to track Claude usage: {e}")
    
    def get_claude_usage(self) -> dict:
        """Get Claude usage statistics."""
        if not self.redis:
            return {"total_calls": 0, "total_tokens": 0, "estimated_cost": 0}
        
        try:
            totals = self.redis.hgetall("claude:totals") or {}
            
            total_calls = int(totals.get("calls", 0))
            input_tokens = int(totals.get("input_tokens", 0))
            output_tokens = int(totals.get("output_tokens", 0))
            
            # Claude Haiku pricing: $0.25/1M input, $1.25/1M output
            estimated_cost = (input_tokens * 0.25 / 1_000_000) + (output_tokens * 1.25 / 1_000_000)
            
            # Get daily breakdown
            daily = {}
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                day_data = self.redis.hgetall(f"claude:daily:{date}") or {}
                if day_data:
                    daily[date] = {
                        "calls": int(day_data.get("calls", 0)),
                        "input_tokens": int(day_data.get("input_tokens", 0)),
                        "output_tokens": int(day_data.get("output_tokens", 0))
                    }
            
            return {
                "total_calls": total_calls,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "estimated_cost": round(estimated_cost, 4),
                "daily": daily
            }
        except Exception as e:
            print(f"Failed to get Claude usage: {e}")
            return {"total_calls": 0, "total_tokens": 0, "estimated_cost": 0}
    
    # ============ Detection Metrics ============
    
    def track_detection(self, action: str, category: str, detector: str):
        """Track a detection event."""
        if not self.redis:
            return
        
        try:
            pipe = self.redis.pipeline()
            
            # Lifetime totals
            pipe.hincrby("metrics:detections", f"{action}:{category}", 1)
            pipe.hincrby("metrics:detections", f"total:{action}", 1)
            pipe.hincrby("metrics:detectors", detector, 1)
            
            # Daily totals
            day_key = self._get_date_key("metrics:daily")
            pipe.hincrby(day_key, f"detection:{action}", 1)
            pipe.hincrby(day_key, f"category:{category}", 1)
            pipe.expire(day_key, 86400 * 30)
            
            pipe.execute()
        except Exception as e:
            print(f"Failed to track detection: {e}")
    
    def track_request(self, endpoint: str, action: str):
        """Track an API request."""
        if not self.redis:
            return
        
        try:
            pipe = self.redis.pipeline()
            
            # Lifetime totals
            pipe.hincrby("metrics:requests", "total", 1)
            pipe.hincrby("metrics:requests", f"endpoint:{endpoint}", 1)
            pipe.hincrby("metrics:requests", f"action:{action}", 1)
            
            # Daily totals
            day_key = self._get_date_key("metrics:daily")
            pipe.hincrby(day_key, "requests", 1)
            pipe.hincrby(day_key, f"action:{action}", 1)
            pipe.expire(day_key, 86400 * 30)
            
            pipe.execute()
        except Exception as e:
            print(f"Failed to track request: {e}")
    
    def get_metrics(self) -> dict:
        """Get all metrics."""
        if not self.redis:
            return {"requests": 0, "detections": {}, "daily": {}}
        
        try:
            requests = self.redis.hgetall("metrics:requests") or {}
            detections = self.redis.hgetall("metrics:detections") or {}
            detectors = self.redis.hgetall("metrics:detectors") or {}
            
            # Parse detections by action
            by_action = {}
            by_category = {}
            for key, val in detections.items():
                if key.startswith("total:"):
                    action = key.split(":")[1]
                    by_action[action] = int(val)
                elif ":" in key:
                    action, category = key.split(":", 1)
                    if category not in by_category:
                        by_category[category] = {"count": 0, "action": action}
                    by_category[category]["count"] += int(val)
            
            # Get daily breakdown
            daily = {}
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                day_data = self.redis.hgetall(f"metrics:daily:{date}") or {}
                if day_data:
                    daily[date] = {k: int(v) for k, v in day_data.items()}
            
            return {
                "total_requests": int(requests.get("total", 0)),
                "analyze_requests": int(requests.get("endpoint:/analyze", 0)),
                "by_action": by_action,
                "by_category": by_category,
                "by_detector": {k: int(v) for k, v in detectors.items()},
                "daily": daily
            }
        except Exception as e:
            print(f"Failed to get metrics: {e}")
            return {"requests": 0, "detections": {}, "daily": {}}


# Global instance
_tracker: Optional[UsageTracker] = None


def get_tracker() -> UsageTracker:
    """Get or create usage tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker
