"""
Universal Restrictor API Server.
Security-hardened: Required auth, restricted CORS, sanitized errors.
"""

import os
import logging
import traceback
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from ..engine import Restrictor
from ..models import PolicyConfig
from ..feedback.storage import get_feedback_storage
from ..feedback.models import FeedbackType, FeedbackRequest
from .middleware import RateLimitMiddleware, require_api_key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize app
app = FastAPI(
    title="Universal Restrictor API",
    description="Model-agnostic content classification for LLM safety",
    version="0.1.0",
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    redoc_url=None,  # Disable redoc
)

# CORS - Restrict to allowed origins
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()]

if not ALLOWED_ORIGINS:
    # Default: no CORS (same-origin only)
    logger.warning("No CORS_ORIGINS set. CORS disabled (same-origin only).")
else:
    logger.info(f"CORS enabled for origins: {ALLOWED_ORIGINS}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["X-API-Key", "Content-Type"],
    )

# Rate limiting
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "60"))
app.add_middleware(RateLimitMiddleware, requests_per_minute=RATE_LIMIT)

# Initialize restrictor
restrictor = Restrictor()
logger.info("Restrictor ready.")


# === Request/Response Models ===

class AnalyzeRequest(BaseModel):
    """Request model for text analysis."""
    text: str = Field(..., min_length=1, max_length=50000)
    detect_pii: bool = True
    detect_toxicity: bool = True
    detect_prompt_injection: bool = True
    detect_finance_intent: bool = True
    pii_types: Optional[List[str]] = None
    toxicity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    pii_confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    
    @validator('text')
    def text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Text cannot be empty')
        return v


class DetectionResponse(BaseModel):
    """Individual detection in response."""
    category: str
    severity: str
    confidence: float
    matched_text: str  # Will be masked for PII
    position: dict
    explanation: str
    detector: str


class AnalyzeResponse(BaseModel):
    """Response model for text analysis."""
    action: str
    request_id: str
    processing_time_ms: float
    summary: dict
    detections: List[DetectionResponse]
    redacted_text: Optional[str] = None


class FeedbackSubmitRequest(BaseModel):
    """Request model for feedback submission."""
    request_id: str = Field(..., min_length=36, max_length=36)
    feedback_type: str
    corrected_category: Optional[str] = None
    comment: Optional[str] = Field(None, max_length=1000)
    
    @validator('request_id')
    def validate_request_id(cls, v):
        """Validate UUID format to prevent enumeration."""
        import re
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        if not uuid_pattern.match(v):
            raise ValueError('Invalid request_id format')
        return v
    
    @validator('feedback_type')
    def validate_feedback_type(cls, v):
        valid_types = ['correct', 'false_positive', 'false_negative', 'category_correction']
        if v not in valid_types:
            raise ValueError(f'feedback_type must be one of: {valid_types}')
        return v


# === Error Handling ===

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with sanitized responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail if isinstance(exc.detail, dict) else {
            "error": "request_failed",
            "message": str(exc.detail)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors without leaking internal details."""
    # Log full error internally
    logger.error(f"Unhandled error: {exc}\n{traceback.format_exc()}")
    
    # Return sanitized response
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An internal error occurred. Please try again later."
        }
    )


# === Helper Functions ===

def mask_pii_in_response(matched_text: str, category: str) -> str:
    """Mask PII in API responses to prevent data exposure."""
    if not category.startswith("pii_"):
        return matched_text
    
    if len(matched_text) <= 4:
        return "***"
    
    # Show first 2 and last 2 characters
    return f"{matched_text[:2]}{'*' * (len(matched_text) - 4)}{matched_text[-2:]}"


# === Endpoints ===

@app.get("/health")
async def health_check():
    """Health check endpoint (no auth required)."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(
    request: AnalyzeRequest,
    tenant: dict = Depends(require_api_key)
):
    """
    Analyze text for PII, toxicity, prompt injection, and finance intent.
    Requires valid API key.
    """
    # Build policy from request
    policy = PolicyConfig(
        detect_pii=request.detect_pii,
        detect_toxicity=request.detect_toxicity,
        detect_prompt_injection=request.detect_prompt_injection,
        detect_finance_intent=request.detect_finance_intent,
        pii_types=request.pii_types,
        toxicity_threshold=request.toxicity_threshold,
        pii_confidence_threshold=request.pii_confidence_threshold,
    )
    
    # Analyze
    result = restrictor.analyze(request.text, policy=policy)
    
    # Cache request for feedback
    storage = get_feedback_storage()
    storage.cache_request(
        request_id=result.request_id,
        input_hash=result.input_hash,
        input_length=len(request.text),
        decision=result.action.value,
        categories=[c.value for c in result.categories_found],
        confidence=result.max_confidence,
        tenant_id=tenant.get("tenant_id")
    )
    
    # Build response with masked PII
    detections = []
    for d in result.detections:
        detections.append(DetectionResponse(
            category=d.category.value,
            severity=d.severity.value,
            confidence=d.confidence,
            matched_text=mask_pii_in_response(d.matched_text, d.category.value),
            position={"start": d.start_pos, "end": d.end_pos},
            explanation=d.explanation,
            detector=d.detector
        ))
    
    return AnalyzeResponse(
        action=result.action.value,
        request_id=result.request_id,
        processing_time_ms=result.processing_time_ms,
        summary={
            "categories_found": [c.value for c in result.categories_found],
            "max_severity": result.max_severity.value if result.max_severity else None,
            "max_confidence": result.max_confidence,
            "detection_count": len(result.detections)
        },
        detections=detections,
        redacted_text=result.redacted_text
    )


@app.post("/analyze/batch")
async def analyze_batch(
    texts: List[str],
    tenant: dict = Depends(require_api_key)
):
    """Analyze multiple texts. Requires valid API key."""
    if len(texts) > 100:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "batch_too_large",
                "message": "Maximum 100 texts per batch"
            }
        )
    
    results = []
    for text in texts:
        if text and text.strip():
            result = restrictor.analyze(text)
            results.append({
                "action": result.action.value,
                "request_id": result.request_id,
                "detection_count": len(result.detections)
            })
    
    return {"results": results, "count": len(results)}


@app.post("/feedback")
async def submit_feedback(
    request: FeedbackSubmitRequest,
    tenant: dict = Depends(require_api_key)
):
    """Submit feedback on a detection. Requires valid API key."""
    storage = get_feedback_storage()
    
    try:
        feedback_type = FeedbackType(request.feedback_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_feedback_type",
                "message": "Invalid feedback type"
            }
        )
    
    record = storage.store_feedback(
        request_id=request.request_id,
        feedback_type=feedback_type,
        corrected_category=request.corrected_category,
        comment=request.comment,
        tenant_id=tenant.get("tenant_id")
    )
    
    if record:
        return {
            "feedback_id": record.feedback_id,
            "status": "recorded",
            "message": "Thank you for your feedback."
        }
    else:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "request_not_found",
                "message": "Request ID not found or expired"
            }
        )


@app.get("/feedback/stats")
async def get_feedback_stats(tenant: dict = Depends(require_api_key)):
    """Get feedback statistics. Requires valid API key."""
    storage = get_feedback_storage()
    return storage.get_feedback_stats(tenant_id=tenant.get("tenant_id"))


@app.get("/categories")
async def list_categories(tenant: dict = Depends(require_api_key)):
    """List all detection categories. Requires valid API key."""
    from ..models import Category
    return {
        "categories": [
            {"name": c.name, "value": c.value}
            for c in Category
        ]
    }


@app.get("/usage")
async def get_usage(tenant: dict = Depends(require_api_key)):
    """Get API usage statistics including Claude API costs."""
    return restrictor.get_api_usage()
