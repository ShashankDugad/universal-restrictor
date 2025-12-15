"""Feedback API routes."""

from fastapi import APIRouter, HTTPException
from ..feedback.models import FeedbackRequest, FeedbackResponse
from ..feedback.storage import get_feedback_storage

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback for a previous analysis request.
    
    Use this to report:
    - False positives (flagged but shouldn't have been)
    - False negatives (missed but should have flagged)  
    - Category corrections (wrong category assigned)
    - Correct detections (to reinforce good behavior)
    """
    storage = get_feedback_storage()
    
    record = storage.store_feedback(
        request_id=request.request_id,
        feedback_type=request.feedback_type,
        corrected_category=request.corrected_category,
        comment=request.comment
    )
    
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Request ID '{request.request_id}' not found. Feedback must be submitted within the same session."
        )
    
    return FeedbackResponse(
        feedback_id=record.feedback_id,
        status="recorded",
        message="Thank you for your feedback. It will help improve our detection accuracy."
    )


@router.get("/stats")
async def get_feedback_stats():
    """Get feedback statistics."""
    storage = get_feedback_storage()
    return storage.get_feedback_stats()
