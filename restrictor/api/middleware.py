"""
API Middleware - Rate limiting and authentication.
"""

import time
import hashlib
from typing import Dict, Optional
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[key] = [t for t in self.requests[key] if t > minute_ago]
        
        # Check limit
        if len(self.requests[key]) >= self.requests_per_minute:
            return False
        
        # Add request
        self.requests[key].append(now)
        return True
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests."""
        now = time.time()
        minute_ago = now - 60
        self.requests[key] = [t for t in self.requests[key] if t > minute_ago]
        return max(0, self.requests_per_minute - len(self.requests[key]))


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute)
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        api_key = request.headers.get("X-API-Key", "")
        key = f"{client_ip}:{api_key}"
        
        # Check rate limit
        if not self.limiter.is_allowed(key):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again later."
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Remaining"] = str(self.limiter.get_remaining(key))
        response.headers["X-RateLimit-Limit"] = str(self.limiter.requests_per_minute)
        
        return response


class APIKeyAuth:
    """Simple API key authentication."""
    
    def __init__(self):
        # In production, load from database/secrets
        self.valid_keys: Dict[str, dict] = {
            "test-api-key-123": {"tenant_id": "test", "tier": "free"},
            "demo-key-456": {"tenant_id": "demo", "tier": "pro"},
        }
    
    def validate(self, api_key: str) -> Optional[dict]:
        """Validate API key and return tenant info."""
        return self.valid_keys.get(api_key)
    
    def hash_key(self, api_key: str) -> str:
        """Hash API key for logging."""
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]


# Global instances
rate_limiter = RateLimiter(requests_per_minute=60)
api_key_auth = APIKeyAuth()


def get_api_key_auth():
    """Get API key auth instance."""
    return api_key_auth
