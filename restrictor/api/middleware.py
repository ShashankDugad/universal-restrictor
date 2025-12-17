"""
API Middleware - Rate limiting and authentication.
Security-hardened: No hardcoded keys, proper validation.
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


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using in-memory storage.
    For production, use Redis-based rate limiting.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier (IP + API key hash)."""
        client_ip = request.client.host if request.client else "unknown"
        api_key = request.headers.get("X-API-Key", "")
        
        # Hash the API key for privacy
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16] if api_key else "nokey"
        return f"{client_ip}:{key_hash}"
    
    async def dispatch(self, request: Request, call_next):
        client_id = self._get_client_id(request)
        current_time = time.time()
        
        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                t for t in self.requests[client_id] 
                if current_time - t < 60
            ]
        else:
            self.requests[client_id] = []
        
        # Check rate limit
        if len(self.requests[client_id]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for client: {client_id[:20]}...")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please retry later.",
                    "retry_after_seconds": 60
                }
            )
        
        # Record request
        self.requests[client_id].append(current_time)
        
        # Add rate limit headers
        response = await call_next(request)
        remaining = self.requests_per_minute - len(self.requests[client_id])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        
        return response


class APIKeyAuth:
    """
    API Key authentication.
    Keys must be configured via environment variables.
    """
    
    def __init__(self):
        self._load_keys()
    
    def _load_keys(self):
        """Load API keys from environment variables."""
        self.keys: Dict[str, dict] = {}
        
        # Load keys from API_KEYS environment variable
        # Format: "key1:tenant1:tier1,key2:tenant2:tier2"
        keys_str = os.getenv("API_KEYS", "")
        
        if keys_str:
            for entry in keys_str.split(","):
                parts = entry.strip().split(":")
                if len(parts) >= 2:
                    key = parts[0].strip()
                    tenant = parts[1].strip()
                    tier = parts[2].strip() if len(parts) > 2 else "free"
                    
                    if len(key) >= 16:  # Minimum key length
                        self.keys[key] = {"tenant_id": tenant, "tier": tier}
                    else:
                        logger.warning(f"Skipping short API key for tenant: {tenant}")
        
        if not self.keys:
            logger.warning("No API keys configured. Set API_KEYS environment variable.")
            logger.warning("Format: API_KEYS='key1:tenant1:tier1,key2:tenant2:tier2'")
    
    def validate(self, api_key: str) -> Tuple[bool, Optional[dict]]:
        """
        Validate API key.
        
        Returns:
            (is_valid, tenant_info)
        """
        if not api_key:
            return False, None
        
        if api_key in self.keys:
            return True, self.keys[api_key]
        
        return False, None
    
    def reload_keys(self):
        """Reload keys from environment (for runtime updates)."""
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
    """
    Dependency that requires valid API key.
    Raises 401 if missing, 403 if invalid.
    """
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
        logger.warning(f"Invalid API key attempt from {request.client.host if request.client else 'unknown'}")
        raise HTTPException(
            status_code=403,
            detail={
                "error": "invalid_api_key",
                "message": "Invalid API key."
            }
        )
    
    return tenant_info


# Backward compatibility alias
verify_api_key = require_api_key
