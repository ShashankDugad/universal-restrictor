"""Feedback data models."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class FeedbackType(str, Enum):
    """Types of feedback users can provide."""
    CORRECT = "correct"                    # Detection was accurate
    FALSE_POSITIVE = "false_positive"      # Flagged but shouldn't have been
    FALSE_NEGATIVE = "false_negative"      # Missed but should have flagged
    CATEGORY_CORRECTION = "category_correction"  # Wrong category assigned


class FeedbackRequest(BaseModel):
    """Request to submit feedback."""
    request_id: str = Field(..., description="Original request ID from /analyze response")
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    corrected_category: Optional[str] = Field(None, description="Correct category (for category_correction)")
    comment: Optional[str] = Field(None, max_length=500, description="Optional comment")


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""
    feedback_id: str
    status: str = "recorded"
    message: str = "Thank you for your feedback"


class FeedbackRecord(BaseModel):
    """Internal feedback record for storage."""
    feedback_id: str
    tenant_id: str = "default"
    request_id: str
    input_hash: str
    input_length: int
    original_decision: str
    original_categories: List[str]
    original_confidence: float
    feedback_type: FeedbackType
    corrected_category: Optional[str] = None
    comment: Optional[str] = None
    timestamp: datetime
    reviewed: bool = False
    included_in_training: bool = False
