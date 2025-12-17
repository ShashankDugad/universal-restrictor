"""Feedback API routes with authentication."""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional

from ..feedback.models import FeedbackRequest, FeedbackResponse
from ..feedback.storage import get_feedback_storage
from .middleware import get_api_key_auth, APIKeyAuth

router = APIRouter(prefix="/feedback", tags=["feedback"])


async def verify_api_key_optional(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    auth: APIKeyAuth = Depends(get_api_key_auth)
) -> dict:
    """Verify API key (optional for feedback)."""
    if x_api_key is None:
        return {"tenant_id": "anonymous", "tier": "free"}
    
    tenant = auth.validate(x_api_key)
    if tenant is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return tenant


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    tenant: dict = Depends(verify_api_key_optional)
):
    """
    Submit feedback for a previous analysis request.
    """
    storage = get_feedback_storage()
    
    record = storage.store_feedback(
        request_id=request.request_id,
        feedback_type=request.feedback_type,
        corrected_category=request.corrected_category,
        comment=request.comment,
        tenant_id=tenant.get("tenant_id", "anonymous")
    )
    
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Request ID '{request.request_id}' not found."
        )
    
    return FeedbackResponse(
        feedback_id=record.feedback_id,
        status="recorded",
        message="Thank you for your feedback."
    )


@router.get("/stats")
async def get_feedback_stats(tenant: dict = Depends(verify_api_key_optional)):
    """Get feedback statistics."""
    storage = get_feedback_storage()
    return storage.get_feedback_stats()
