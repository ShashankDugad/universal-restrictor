"""Feedback storage - local JSON file for MVP, DynamoDB for production."""

import json
import os
import uuid
import hashlib
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

from .models import FeedbackRecord, FeedbackType


class FeedbackStorage:
    """
    Store feedback locally for MVP.
    
    Production: Replace with DynamoDB.
    """
    
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            storage_path = os.path.join(
                os.path.dirname(__file__), 
                "..", "..", "data", "feedback.json"
            )
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Request cache: stores recent requests for feedback linking
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
        # Limit cache size
        if len(self._request_cache) >= self._cache_max_size:
            # Remove oldest 10%
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
        """
        Store feedback for a request.
        
        Returns FeedbackRecord if successful, None if request not found.
        """
        # Get cached request
        cached = self._request_cache.get(request_id)
        if not cached:
            return None
        
        # Create feedback record
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
        
        # Load existing feedback
        feedback_list = self._load_feedback()
        
        # Add new record
        feedback_list.append(record.model_dump(mode="json"))
        
        # Save
        self._save_feedback(feedback_list)
        
        return record
    
    def get_feedback_stats(self) -> dict:
        """Get feedback statistics."""
        feedback_list = self._load_feedback()
        
        if not feedback_list:
            return {
                "total": 0,
                "by_type": {},
                "reviewed": 0,
                "pending_review": 0
            }
        
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
        
        return [
            fb for fb in feedback_list 
            if not fb.get("included_in_training")
        ][:limit]
    
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


# Singleton instance
_storage_instance = None

def get_feedback_storage() -> FeedbackStorage:
    """Get global feedback storage instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = FeedbackStorage()
    return _storage_instance
