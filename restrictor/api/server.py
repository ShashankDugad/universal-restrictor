"""
FastAPI server for Universal Restrictor API.
"""

import hashlib
import time
import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..engine import Restrictor
from ..models import Action, PolicyConfig
from ..feedback.storage import get_feedback_storage
from .feedback_routes import router as feedback_router
from .middleware import RateLimitMiddleware, get_api_key_auth, APIKeyAuth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global restrictor instance
restrictor: Optional[Restrictor] = None


def get_restrictor() -> Restrictor:
    """Get restrictor instance."""
    global restrictor
    if restrictor is None:
        restrictor = Restrictor()
    return restrictor


async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    auth: APIKeyAuth = Depends(get_api_key_auth)
) -> dict:
    """Verify API key and return tenant info."""
    # Allow unauthenticated access for now (MVP)
    if x_api_key is None:
        return {"tenant_id": "anonymous", "tier": "free"}
    
    tenant = auth.validate(x_api_key)
    if tenant is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return tenant


app = FastAPI(
    title="Universal Restrictor API",
    description="Model-agnostic content classification API for LLM safety",
    version="0.1.0",
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include feedback routes
app.include_router(feedback_router)


# Request/Response models
class AnalyzeRequest(BaseModel):
    """Request to analyze text."""
    text: str = Field(..., min_length=1, max_length=100000)
    detect_pii: bool = True
    detect_toxicity: bool = True
    detect_prompt_injection: bool = True
    detect_finance_intent: bool = True
    pii_types: Optional[List[str]] = None
    toxicity_threshold: float = Field(0.7, ge=0.0, le=1.0)
    pii_confidence_threshold: float = Field(0.8, ge=0.0, le=1.0)


class DetectionDetail(BaseModel):
    """Details of a single detection."""
    category: str
    severity: str
    confidence: float
    matched_text: str
    position: dict
    explanation: str
    detector: str


class AnalyzeSummary(BaseModel):
    """Summary of analysis results."""
    categories_found: List[str]
    max_severity: Optional[str]
    max_confidence: float
    detection_count: int


class AnalyzeResponse(BaseModel):
    """Response from analyze endpoint."""
    action: str
    request_id: str
    processing_time_ms: float
    summary: AnalyzeSummary
    detections: List[DetectionDetail]
    redacted_text: Optional[str] = None


class BatchRequest(BaseModel):
    """Request to analyze multiple texts."""
    texts: List[str] = Field(..., min_length=1, max_length=100)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    detectors: dict


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    global restrictor
    logger.info("Initializing Universal Restrictor...")
    restrictor = Restrictor()
    logger.info("Restrictor ready.")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and detector status."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        detectors={
            "pii": "active",
            "toxicity": "active",
            "prompt_injection": "active",
            "finance_intent": "active"
        }
    )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(
    request: AnalyzeRequest,
    tenant: dict = Depends(verify_api_key)
):
    """
    Analyze text for PII, toxicity, and prompt injection.
    
    Returns detection results with action recommendation.
    """
    r = get_restrictor()
    
    start_time = time.time()
    
    # Build policy from request
    policy = PolicyConfig(
        detect_pii=request.detect_pii,
        detect_toxicity=request.detect_toxicity,
        detect_prompt_injection=request.detect_prompt_injection,
        detect_finance_intent=request.detect_finance_intent,
        toxicity_threshold=request.toxicity_threshold,
        pii_confidence_threshold=request.pii_confidence_threshold,
        pii_types=request.pii_types,
    )
    
    # Run analysis
    result = r.analyze(text=request.text, policy=policy)
    
    processing_time = (time.time() - start_time) * 1000
    
    # Build response
    detections = [
        DetectionDetail(
            category=d.category.value,
            severity=d.severity.value,
            confidence=d.confidence,
            matched_text=d.matched_text,
            position={"start": d.start_pos, "end": d.end_pos},
            explanation=d.explanation,
            detector=d.detector
        )
        for d in result.detections
    ]
    
    categories = [c.value for c in result.categories_found]
    
    # Cache request for feedback
    input_hash = hashlib.sha256(request.text.encode()).hexdigest()
    feedback_storage = get_feedback_storage()
    feedback_storage.cache_request(
        request_id=result.request_id,
        input_hash=input_hash,
        input_length=len(request.text),
        decision=result.action.value,
        categories=categories,
        confidence=result.max_confidence
    )
    
    return AnalyzeResponse(
        action=result.action.value,
        request_id=result.request_id,
        processing_time_ms=processing_time,
        summary=AnalyzeSummary(
            categories_found=categories,
            max_severity=result.max_severity.value if result.max_severity else None,
            max_confidence=result.max_confidence,
            detection_count=len(detections)
        ),
        detections=detections,
        redacted_text=result.redacted_text
    )


@app.post("/analyze/batch")
async def analyze_batch(
    request: BatchRequest,
    tenant: dict = Depends(verify_api_key)
):
    """Analyze multiple texts in one request."""
    r = get_restrictor()
    
    results = []
    for text in request.texts:
        result = r.analyze(text=text)
        results.append({
            "action": result.action.value,
            "request_id": result.request_id,
            "detection_count": len(result.detections)
        })
    
    return {"results": results, "count": len(results)}


@app.get("/categories")
async def list_categories():
    """List all detection categories."""
    from ..models import Category
    return {
        "categories": [
            {"name": c.name, "value": c.value}
            for c in Category
        ]
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )
