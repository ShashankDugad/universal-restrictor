"""
Redis-based feedback storage with tenant support.
"""

import os
import json
import logging
from typing import Optional, List
from datetime import datetime, timedelta

from .models import FeedbackType, FeedbackRecord

logger = logging.getLogger(__name__)


class RedisFeedbackStorage:
    """Redis-backed storage for feedback with multi-tenant support."""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis."""
        try:
            import redis
            self._client = redis.from_url(self.redis_url)
            self._client.ping()
            logger.info(f"Connected to Redis: {self.redis_url}")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self._client = None
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Redis."""
        if self._client is None:
            return False
        try:
            self._client.ping()
            return True
        except:
            return False
    
    def cache_request(
        self,
        request_id: str,
        input_hash: str,
        input_length: int,
        decision: str,
        categories: List[str],
        confidence: float,
        tenant_id: str = None
    ):
        """Cache request details for later feedback."""
        if not self.is_connected:
            return
        
        key = f"request_cache:{request_id}"
        data = {
            "request_id": request_id,
            "input_hash": input_hash,
            "input_length": input_length,
            "decision": decision,
            "categories": categories,
            "confidence": confidence,
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            self._client.setex(key, timedelta(hours=1), json.dumps(data))
        except Exception as e:
            logger.error(f"Failed to cache request: {e}")
    
    def get_cached_request(self, request_id: str) -> Optional[dict]:
        """Get cached request details."""
        if not self.is_connected:
            return None
        
        try:
            key = f"request_cache:{request_id}"
            data = self._client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Failed to get cached request: {e}")
        
        return None
    
    def store_feedback(
        self,
        request_id: str,
        feedback_type: FeedbackType,
        corrected_category: str = None,
        comment: str = None,
        tenant_id: str = None
    ) -> Optional[FeedbackRecord]:
        """Store feedback for a request."""
        if not self.is_connected:
            return None
        
        # Get cached request
        cached = self.get_cached_request(request_id)
        if not cached:
            logger.warning(f"Request {request_id} not found in cache")
            return None
        
        # Create feedback record
        import uuid
        feedback_id = f"fb_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        record = FeedbackRecord(
            feedback_id=feedback_id,
            tenant_id=tenant_id or cached.get("tenant_id"),
            request_id=request_id,
            input_hash=cached.get("input_hash", ""),
            input_length=cached.get("input_length", 0),
            original_decision=cached.get("decision", ""),
            original_categories=cached.get("categories", []),
            original_confidence=cached.get("confidence", 0.0),
            feedback_type=feedback_type.value,
            corrected_category=corrected_category,
            comment=comment,
            timestamp=now,
            reviewed=False,
            included_in_training=False
        )
        
        try:
            # Convert to dict and ensure all values are JSON serializable
            record_dict = {
                "feedback_id": record.feedback_id,
                "tenant_id": record.tenant_id,
                "request_id": record.request_id,
                "input_hash": record.input_hash,
                "input_length": record.input_length,
                "original_decision": record.original_decision,
                "original_categories": record.original_categories,
                "original_confidence": record.original_confidence,
                "feedback_type": record.feedback_type,
                "corrected_category": record.corrected_category,
                "comment": record.comment,
                "timestamp": now,
                "reviewed": record.reviewed,
                "included_in_training": record.included_in_training,
            }
            
            # Store feedback
            key = f"feedback:{feedback_id}"
            self._client.set(key, json.dumps(record_dict))
            
            # Add to indexes
            self._client.sadd("feedback:all", feedback_id)
            self._client.sadd(f"feedback:index:request:{request_id}", feedback_id)
            
            if record.tenant_id:
                self._client.sadd(f"feedback:index:tenant:{record.tenant_id}", feedback_id)
            
            # Invalidate stats cache
            self._client.delete("feedback:stats")
            
            logger.info(f"Stored feedback {feedback_id} for request {request_id}")
            return record
            
        except Exception as e:
            logger.error(f"Failed to store feedback: {e}")
            return None
    
    def get_feedback_stats(self, tenant_id: str = None) -> dict:
        """Get feedback statistics."""
        if not self.is_connected:
            return {"total": 0, "by_type": {}, "reviewed": 0, "pending_review": 0}
        
        try:
            # Check cache first (tenant-specific)
            cache_key = f"feedback:stats:{tenant_id}" if tenant_id else "feedback:stats"
            cached = self._client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Get all feedback IDs for tenant
            if tenant_id:
                feedback_ids = self._client.smembers(f"feedback:index:tenant:{tenant_id}")
            else:
                feedback_ids = self._client.smembers("feedback:all")
            
            stats = {
                "total": len(feedback_ids),
                "by_type": {},
                "reviewed": 0,
                "pending_review": 0
            }
            
            for fid in feedback_ids:
                fid = fid.decode() if isinstance(fid, bytes) else fid
                data = self._client.get(f"feedback:{fid}")
                if data:
                    record = json.loads(data)
                    ftype = record.get("feedback_type", "unknown")
                    stats["by_type"][ftype] = stats["by_type"].get(ftype, 0) + 1
                    
                    if record.get("reviewed"):
                        stats["reviewed"] += 1
                    else:
                        stats["pending_review"] += 1
            
            # Cache for 5 minutes
            self._client.setex(cache_key, 300, json.dumps(stats))
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get feedback stats: {e}")
            return {"total": 0, "by_type": {}, "reviewed": 0, "pending_review": 0}
    
    def get_feedback_for_training(self, limit: int = 1000) -> List[dict]:
        """Get reviewed feedback for model training."""
        if not self.is_connected:
            return []
        
        try:
            feedback_ids = self._client.smembers("feedback:all")
            training_data = []
            
            for fid in feedback_ids:
                if len(training_data) >= limit:
                    break
                    
                fid = fid.decode() if isinstance(fid, bytes) else fid
                data = self._client.get(f"feedback:{fid}")
                if data:
                    record = json.loads(data)
                    if record.get("reviewed") and not record.get("included_in_training"):
                        training_data.append(record)
            
            return training_data
            
        except Exception as e:
            logger.error(f"Failed to get training data: {e}")
            return []
