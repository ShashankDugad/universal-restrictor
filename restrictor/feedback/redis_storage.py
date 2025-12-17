"""
Redis-backed feedback storage for production.
Persistent across restarts, supports multi-instance deployment.
"""

import json
import os
import uuid
import hashlib
from datetime import datetime
from typing import Optional, List, Dict
import logging

from .models import FeedbackRecord, FeedbackType

logger = logging.getLogger(__name__)


class RedisFeedbackStorage:
    """
    Redis-backed feedback storage.
    
    Keys:
    - feedback:{feedback_id} -> FeedbackRecord JSON
    - feedback:index:request:{request_id} -> Set of feedback_ids
    - feedback:index:tenant:{tenant_id} -> Set of feedback_ids
    - request_cache:{request_id} -> Request details (TTL 1 hour)
    - feedback:stats -> Cached stats (TTL 5 min)
    """
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client = None
        self._cache_ttl = 3600  # 1 hour for request cache
        self._stats_ttl = 300   # 5 min for stats cache
    
    @property
    def client(self):
        """Lazy Redis connection."""
        if self._client is None:
            try:
                import redis
                self._client = redis.from_url(self.redis_url, decode_responses=True)
                self._client.ping()
                logger.info(f"Connected to Redis: {self.redis_url}")
            except Exception as e:
                logger.warning(f"Redis unavailable: {e}. Using fallback.")
                self._client = None
        return self._client
    
    def cache_request(
        self,
        request_id: str,
        input_hash: str,
        input_length: int,
        decision: str,
        categories: List[str],
        confidence: float
    ):
        """Cache request details for feedback linking."""
        if self.client is None:
            return
        
        data = {
            "input_hash": input_hash,
            "input_length": input_length,
            "decision": decision,
            "categories": categories,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            self.client.setex(
                f"request_cache:{request_id}",
                self._cache_ttl,
                json.dumps(data)
            )
        except Exception as e:
            logger.error(f"Redis cache_request error: {e}")
    
    def store_feedback(
        self,
        request_id: str,
        feedback_type: FeedbackType,
        corrected_category: Optional[str] = None,
        comment: Optional[str] = None,
        tenant_id: str = "default"
    ) -> Optional[FeedbackRecord]:
        """Store feedback for a request."""
        if self.client is None:
            return None
        
        try:
            # Get cached request
            cached_data = self.client.get(f"request_cache:{request_id}")
            if not cached_data:
                return None
            
            cached = json.loads(cached_data)
            
            # Check for duplicate
            existing_ids = self.client.smembers(f"feedback:index:request:{request_id}")
            for fid in existing_ids:
                existing = self.client.get(f"feedback:{fid}")
                if existing:
                    existing_record = json.loads(existing)
                    if existing_record.get("feedback_type") == feedback_type.value:
                        # Return existing record
                        return FeedbackRecord(
                            feedback_id=existing_record["feedback_id"],
                            tenant_id=existing_record["tenant_id"],
                            request_id=existing_record["request_id"],
                            input_hash=existing_record["input_hash"],
                            input_length=existing_record["input_length"],
                            original_decision=existing_record["original_decision"],
                            original_categories=existing_record["original_categories"],
                            original_confidence=existing_record["original_confidence"],
                            feedback_type=FeedbackType(existing_record["feedback_type"]),
                            corrected_category=existing_record.get("corrected_category"),
                            comment=existing_record.get("comment"),
                            timestamp=datetime.fromisoformat(existing_record["timestamp"]),
                            reviewed=existing_record.get("reviewed", False),
                            included_in_training=existing_record.get("included_in_training", False)
                        )
            
            # Create new feedback record
            feedback_id = f"fb_{uuid.uuid4().hex[:12]}"
            
            record = FeedbackRecord(
                feedback_id=feedback_id,
                tenant_id=tenant_id,
                request_id=request_id,
                input_hash=cached["input_hash"],
                input_length=cached["input_length"],
                original_decision=cached["decision"],
                original_categories=cached["categories"],
                original_confidence=cached["confidence"],
                feedback_type=feedback_type,
                corrected_category=corrected_category,
                comment=comment,
                timestamp=datetime.utcnow(),
                reviewed=False,
                included_in_training=False
            )
            
            # Store in Redis
            record_data = {
                "feedback_id": record.feedback_id,
                "tenant_id": record.tenant_id,
                "request_id": record.request_id,
                "input_hash": record.input_hash,
                "input_length": record.input_length,
                "original_decision": record.original_decision,
                "original_categories": record.original_categories,
                "original_confidence": record.original_confidence,
                "feedback_type": record.feedback_type.value,
                "corrected_category": record.corrected_category,
                "comment": record.comment,
                "timestamp": record.timestamp.isoformat(),
                "reviewed": record.reviewed,
                "included_in_training": record.included_in_training
            }
            
            # Store record
            self.client.set(f"feedback:{feedback_id}", json.dumps(record_data))
            
            # Add to indexes
            self.client.sadd(f"feedback:index:request:{request_id}", feedback_id)
            self.client.sadd(f"feedback:index:tenant:{tenant_id}", feedback_id)
            self.client.sadd("feedback:all", feedback_id)
            
            # Invalidate stats cache
            self.client.delete("feedback:stats")
            
            return record
            
        except Exception as e:
            logger.error(f"Redis store_feedback error: {e}")
            return None
    
    def get_feedback_stats(self) -> dict:
        """Get feedback statistics."""
        if self.client is None:
            return {"total": 0, "by_type": {}, "reviewed": 0, "pending_review": 0}
        
        try:
            # Check cache
            cached = self.client.get("feedback:stats")
            if cached:
                return json.loads(cached)
            
            # Calculate stats
            all_ids = self.client.smembers("feedback:all")
            
            if not all_ids:
                return {"total": 0, "by_type": {}, "reviewed": 0, "pending_review": 0}
            
            by_type = {}
            reviewed = 0
            
            for fid in all_ids:
                data = self.client.get(f"feedback:{fid}")
                if data:
                    record = json.loads(data)
                    fb_type = record.get("feedback_type", "unknown")
                    by_type[fb_type] = by_type.get(fb_type, 0) + 1
                    if record.get("reviewed"):
                        reviewed += 1
            
            stats = {
                "total": len(all_ids),
                "by_type": by_type,
                "reviewed": reviewed,
                "pending_review": len(all_ids) - reviewed
            }
            
            # Cache stats
            self.client.setex("feedback:stats", self._stats_ttl, json.dumps(stats))
            
            return stats
            
        except Exception as e:
            logger.error(f"Redis get_feedback_stats error: {e}")
            return {"total": 0, "by_type": {}, "reviewed": 0, "pending_review": 0}
    
    def get_feedback_for_training(self, limit: int = 1000) -> List[dict]:
        """Get unprocessed feedback for training."""
        if self.client is None:
            return []
        
        try:
            all_ids = self.client.smembers("feedback:all")
            results = []
            
            for fid in all_ids:
                if len(results) >= limit:
                    break
                    
                data = self.client.get(f"feedback:{fid}")
                if data:
                    record = json.loads(data)
                    if not record.get("included_in_training"):
                        results.append(record)
            
            return results
            
        except Exception as e:
            logger.error(f"Redis get_feedback_for_training error: {e}")
            return []
    
    def mark_as_trained(self, feedback_ids: List[str]):
        """Mark feedback as included in training."""
        if self.client is None:
            return
        
        try:
            for fid in feedback_ids:
                data = self.client.get(f"feedback:{fid}")
                if data:
                    record = json.loads(data)
                    record["included_in_training"] = True
                    self.client.set(f"feedback:{fid}", json.dumps(record))
            
            # Invalidate stats cache
            self.client.delete("feedback:stats")
            
        except Exception as e:
            logger.error(f"Redis mark_as_trained error: {e}")
