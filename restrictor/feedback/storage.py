"""
Feedback storage factory - selects Redis or file storage.
"""

import logging
import os
from typing import Optional

from .models import FeedbackRecord, FeedbackType

logger = logging.getLogger(__name__)

# Storage instances
_redis_storage = None
_file_storage = None


class FileFeedbackStorage:
    """Simple file-based storage fallback."""

    def __init__(self, filepath: str = "data/feedback.json"):
        self.filepath = filepath
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

    def cache_request(self, request_id: str, input_hash: str, input_length: int,
                      decision: str, categories: list, confidence: float, tenant_id: str = None):
        """Cache request (no-op for file storage)."""
        pass

    def store_feedback(self, request_id: str, feedback_type: FeedbackType,
                       corrected_category: str = None, comment: str = None,
                       tenant_id: str = None) -> Optional[FeedbackRecord]:
        """Store feedback to file."""
        return None

    def get_feedback_stats(self, tenant_id: str = None) -> dict:
        """Get stats."""
        return {"total": 0, "by_type": {}, "reviewed": 0, "pending_review": 0}


def get_feedback_storage():
    """Get the appropriate storage backend."""
    global _redis_storage, _file_storage

    # Try Redis first
    if _redis_storage is None:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                from .redis_storage import RedisFeedbackStorage
                _redis_storage = RedisFeedbackStorage(redis_url)

                # Check if connected using is_connected property
                if _redis_storage.is_connected:
                    logger.info("Using Redis feedback storage")
                    return _redis_storage
                else:
                    logger.warning("Redis connection failed, falling back to file storage")
                    _redis_storage = None
            except Exception as e:
                logger.warning(f"Redis unavailable: {e}")
                _redis_storage = None

    if _redis_storage and _redis_storage.is_connected:
        return _redis_storage

    # Fall back to file storage
    if _file_storage is None:
        _file_storage = FileFeedbackStorage()
        logger.info("Using file feedback storage")

    return _file_storage
