"""
Feedback storage - Redis for production, JSON file fallback.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path
import logging

from .models import FeedbackRecord, FeedbackType

logger = logging.getLogger(__name__)

# Try Redis first
_redis_storage = None
_file_storage = None


def get_feedback_storage():
    """Get best available storage backend."""
    global _redis_storage, _file_storage
    
    # Try Redis first
    if _redis_storage is None:
        try:
            from .redis_storage import RedisFeedbackStorage
            _redis_storage = RedisFeedbackStorage()
            if _redis_storage.client is not None:
                logger.info("Using Redis feedback storage")
                return _redis_storage
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}")
    
    if _redis_storage and _redis_storage.client is not None:
        return _redis_storage
    
    # Fallback to file storage
    if _file_storage is None:
        _file_storage = FileFeedbackStorage()
        logger.info("Using file-based feedback storage")
    
    return _file_storage


class FileFeedbackStorage:
    """
    File-based feedback storage (fallback).
    """
    
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            storage_path = os.path.join(
                os.path.dirname(__file__), 
                "..", "..", "data", "feedback.json"
            )
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._request_cache: Dict[str, dict] = {}
        self._cache_max_size = 10000
    
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
        if len(self._request_cache) >= self._cache_max_size:
            keys = list(self._request_cache.keys())
            for k in keys[:len(keys)//10]:
                del self._request_cache[k]
        
        self._request_cache[request_id] = {
            "input_hash": input_hash,
            "input_length": input_length,
            "decision": decision,
            "categories": categories,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def store_feedback(
        self,
        request_id: str,
        feedback_type: FeedbackType,
        corrected_category: Optional[str] = None,
        comment: Optional[str] = None,
        tenant_id: str = "default"
    ) -> Optional[FeedbackRecord]:
        """Store feedback for a request."""
        cached = self._request_cache.get(request_id)
        if not cached:
            return None
        
        feedback_list = self._load_feedback()
        
        # Check for duplicate
        for existing in feedback_list:
            if (existing.get("request_id") == request_id and 
                existing.get("feedback_type") == feedback_type.value):
                return FeedbackRecord(
                    feedback_id=existing["feedback_id"],
                    tenant_id=existing["tenant_id"],
                    request_id=existing["request_id"],
                    input_hash=existing["input_hash"],
                    input_length=existing["input_length"],
                    original_decision=existing["original_decision"],
                    original_categories=existing["original_categories"],
                    original_confidence=existing["original_confidence"],
                    feedback_type=FeedbackType(existing["feedback_type"]),
                    corrected_category=existing.get("corrected_category"),
                    comment=existing.get("comment"),
                    timestamp=datetime.fromisoformat(existing["timestamp"]),
                    reviewed=existing.get("reviewed", False),
                    included_in_training=existing.get("included_in_training", False)
                )
        
        record = FeedbackRecord(
            feedback_id=f"fb_{uuid.uuid4().hex[:12]}",
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
        
        feedback_list.append(record.model_dump(mode="json"))
        self._save_feedback(feedback_list)
        
        return record
    
    def get_feedback_stats(self) -> dict:
        """Get feedback statistics."""
        feedback_list = self._load_feedback()
        
        if not feedback_list:
            return {"total": 0, "by_type": {}, "reviewed": 0, "pending_review": 0}
        
        by_type = {}
        reviewed = 0
        
        for fb in feedback_list:
            fb_type = fb.get("feedback_type", "unknown")
            by_type[fb_type] = by_type.get(fb_type, 0) + 1
            if fb.get("reviewed"):
                reviewed += 1
        
        return {
            "total": len(feedback_list),
            "by_type": by_type,
            "reviewed": reviewed,
            "pending_review": len(feedback_list) - reviewed
        }
    
    def get_feedback_for_training(self, limit: int = 1000) -> List[dict]:
        """Get unprocessed feedback for training."""
        feedback_list = self._load_feedback()
        return [fb for fb in feedback_list if not fb.get("included_in_training")][:limit]
    
    def mark_as_trained(self, feedback_ids: List[str]):
        """Mark feedback as included in training."""
        feedback_list = self._load_feedback()
        
        for fb in feedback_list:
            if fb.get("feedback_id") in feedback_ids:
                fb["included_in_training"] = True
        
        self._save_feedback(feedback_list)
    
    def _load_feedback(self) -> List[dict]:
        """Load feedback from file."""
        if not self.storage_path.exists():
            return []
        
        try:
            with open(self.storage_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_feedback(self, feedback_list: List[dict]):
        """Save feedback to file."""
        with open(self.storage_path, "w") as f:
            json.dump(feedback_list, f, indent=2, default=str)
