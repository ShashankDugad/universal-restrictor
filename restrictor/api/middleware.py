"""
API Middleware - Rate limiting and authentication.
Security-hardened: Redis rate limiting, no hardcoded keys.
"""

import os
import time
import logging
import hashlib
from typing import Dict, Optional, Tuple
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """Redis-based rate limiter for distributed deployments."""
    
    def __init__(self, redis_url: str = None, requests_per_minute: int = 60):
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self.requests_per_minute = requests_per_minute
        self._client = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis."""
        if not self.redis_url:
            return
        try:
            import redis
            self._client = redis.from_url(self.redis_url)
            self._client.ping()
            logger.info("Redis rate limiter connected")
        except Exception as e:
            logger.warning(f"Redis rate limiter unavailable: {e}")
            self._client = None
    
    @property
    def is_connected(self) -> bool:
        if self._client is None:
            return False
        try:
            self._client.ping()
            return True
        except:
            return False
    
    def check_rate_limit(self, client_id: str) -> Tuple[bool, int, int]:
        """
        Check if request is allowed.
        
        Returns:
            (allowed, remaining, reset_seconds)
        """
        if not self.is_connected:
            return True, self.requests_per_minute, 60
        
        key = f"ratelimit:{client_id}"
        current_time = int(time.time())
        window_start = current_time - 60
        
        try:
            pipe = self._client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiry
            pipe.expire(key, 120)
            
            results = pipe.execute()
            request_count = results[1]
            
            remaining = max(0, self.requests_per_minute - request_count - 1)
            allowed = request_count < self.requests_per_minute
            
            return allowed, remaining, 60
            
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            return True, self.requests_per_minute, 60


class InMemoryRateLimiter:
    """In-memory rate limiter for single-instance deployments."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}
    
    def check_rate_limit(self, client_id: str) -> Tuple[bool, int, int]:
        """Check if request is allowed."""
        current_time = time.time()
        
        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                t for t in self.requests[client_id]
                if current_time - t < 60
            ]
        else:
            self.requests[client_id] = []
        
        request_count = len(self.requests[client_id])
        
        if request_count >= self.requests_per_minute:
            return False, 0, 60
        
        self.requests[client_id].append(current_time)
        remaining = self.requests_per_minute - request_count - 1
        
        return True, remaining, 60


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter(requests_per_minute: int = 60):
    """Get or create rate limiter (Redis preferred, fallback to memory)."""
    global _rate_limiter
    
    if _rate_limiter is None:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            _rate_limiter = RedisRateLimiter(redis_url, requests_per_minute)
            if _rate_limiter.is_connected:
                logger.info("Using Redis rate limiter")
                return _rate_limiter
        
        _rate_limiter = InMemoryRateLimiter(requests_per_minute)
        logger.info("Using in-memory rate limiter")
    
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with Redis support."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.limiter = get_rate_limiter(requests_per_minute)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier (IP + API key hash)."""
        client_ip = request.client.host if request.client else "unknown"
        api_key = request.headers.get("X-API-Key", "")
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16] if api_key else "nokey"
        return f"{client_ip}:{key_hash}"
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)
        
        client_id = self._get_client_id(request)
        allowed, remaining, reset = self.limiter.check_rate_limit(client_id)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for: {client_id[:20]}...")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please retry later.",
                    "retry_after_seconds": reset
                },
                headers={
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset),
                    "Retry-After": str(reset)
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset)
        
        return response


class APIKeyAuth:
    """API Key authentication from environment variables."""
    
    def __init__(self):
        self._load_keys()
    
    def _load_keys(self):
        """Load API keys from environment."""
        self.keys: Dict[str, dict] = {}
        keys_str = os.getenv("API_KEYS", "")
        
        if keys_str:
            for entry in keys_str.split(","):
                parts = entry.strip().split(":")
                if len(parts) >= 2:
                    key = parts[0].strip()
                    tenant = parts[1].strip()
                    tier = parts[2].strip() if len(parts) > 2 else "free"
                    
                    if len(key) >= 16:
                        self.keys[key] = {"tenant_id": tenant, "tier": tier}
                    else:
                        logger.warning(f"Skipping short API key for tenant: {tenant}")
        
        if not self.keys:
            logger.warning("No API keys configured. Set API_KEYS env var.")
    
    def validate(self, api_key: str) -> Tuple[bool, Optional[dict]]:
        """Validate API key."""
        if not api_key:
            return False, None
        if api_key in self.keys:
            return True, self.keys[api_key]
        return False, None
    
    def reload_keys(self):
        """Reload keys from environment."""
        self._load_keys()


# Global auth instance
_auth_instance: Optional[APIKeyAuth] = None


def get_auth() -> APIKeyAuth:
    """Get or create auth instance."""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = APIKeyAuth()
    return _auth_instance


async def require_api_key(request: Request) -> dict:
    """Dependency that requires valid API key."""
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        logger.warning(f"Missing API key from {request.client.host if request.client else 'unknown'}")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "authentication_required",
                "message": "API key required. Include X-API-Key header."
            }
        )
    
    auth = get_auth()
    is_valid, tenant_info = auth.validate(api_key)
    
    if not is_valid:
        logger.warning(f"Invalid API key from {request.client.host if request.client else 'unknown'}")
        raise HTTPException(
            status_code=403,
            detail={
                "error": "invalid_api_key",
                "message": "Invalid API key."
            }
        )
    
    return tenant_info


verify_api_key = require_api_key


# =============================================================================
# Prometheus Metrics Middleware
# =============================================================================

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to record Prometheus metrics for all requests."""
    
    async def dispatch(self, request: Request, call_next):
        from restrictor.api.metrics import record_request, ACTIVE_REQUESTS
        
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)
        
        ACTIVE_REQUESTS.inc()
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Record metrics
            record_request(
                endpoint=request.url.path,
                method=request.method,
                status=response.status_code,
                duration=duration
            )
            
            return response
        finally:
            ACTIVE_REQUESTS.dec()
