"""
Universal Restrictor API Server

REST API for content classification.
Run with: uvicorn restrictor.api.server:app --reload
"""

import time
import logging
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..engine import Restrictor
from ..models import PolicyConfig, Action, Category

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global restrictor instance
restrictor: Optional[Restrictor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize restrictor on startup."""
    global restrictor
    logger.info("Initializing Universal Restrictor...")
    restrictor = Restrictor()
    logger.info("Restrictor ready.")
    yield
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Universal Restrictor API",
    description="Model-agnostic content classification for LLM applications. Detects PII, toxicity, and prompt injection.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# Request/Response Models
# ==============================================================================

class AnalyzeRequest(BaseModel):
    """Request body for /analyze endpoint."""
    
    text: str = Field(..., description="Text to analyze", min_length=1, max_length=100000)
    
    # Optional policy overrides
    detect_pii: bool = Field(True, description="Enable PII detection")
    detect_toxicity: bool = Field(True, description="Enable toxicity detection")
    detect_prompt_injection: bool = Field(True, description="Enable prompt injection detection")
    
    # Optional thresholds
    toxicity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Toxicity confidence threshold")
    pii_confidence_threshold: float = Field(0.8, ge=0.0, le=1.0, description="PII confidence threshold")
    
    # Custom blocked terms
    blocked_terms: List[str] = Field(default_factory=list, description="Custom terms to block")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Contact me at john@example.com for more details.",
                "detect_pii": True,
                "detect_toxicity": True,
                "detect_prompt_injection": True,
            }
        }


class DetectionItem(BaseModel):
    """A single detection in the response."""
    
    category: str
    severity: str
    confidence: float
    matched_text: str
    position: dict
    explanation: str
    detector: str


class AnalyzeResponse(BaseModel):
    """Response body for /analyze endpoint."""
    
    action: str = Field(..., description="Action to take: allow, allow_warn, redact, block")
    request_id: str = Field(..., description="Unique request identifier for audit")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    
    summary: dict = Field(..., description="Summary of detections")
    detections: List[DetectionItem] = Field(..., description="Detailed detection results")
    
    redacted_text: Optional[str] = Field(None, description="Redacted version of input (if action=redact)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "redact",
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "processing_time_ms": 12.5,
                "summary": {
                    "categories_found": ["pii_email"],
                    "max_severity": "medium",
                    "max_confidence": 0.95,
                    "detection_count": 1
                },
                "detections": [
                    {
                        "category": "pii_email",
                        "severity": "medium",
                        "confidence": 0.95,
                        "matched_text": "john@example.com",
                        "position": {"start": 14, "end": 30},
                        "explanation": "Email address detected",
                        "detector": "pii_regex"
                    }
                ],
                "redacted_text": "Contact me at [REDACTED] for more details."
            }
        }


class BatchAnalyzeRequest(BaseModel):
    """Request body for /analyze/batch endpoint."""
    
    texts: List[str] = Field(..., description="List of texts to analyze", min_items=1, max_items=100)
    
    detect_pii: bool = True
    detect_toxicity: bool = True
    detect_prompt_injection: bool = True


class HealthResponse(BaseModel):
    """Response for health check."""
    
    status: str
    version: str
    detectors: dict


# ==============================================================================
# Middleware
# ==============================================================================

@app.middleware("http")
async def add_request_timing(request: Request, call_next):
    """Add timing header to all responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = str(round(process_time, 2))
    return response


# ==============================================================================
# Endpoints
# ==============================================================================

@app.get("/", include_in_schema=False)
async def root():
    """Redirect to docs."""
    return {"message": "Universal Restrictor API", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint.
    
    Returns service status and loaded detectors.
    """
    if restrictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )
    
    stats = restrictor.get_stats()
    
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        detectors=stats["detectors_loaded"]
    )


@app.post("/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
async def analyze_text(request: AnalyzeRequest):
    """
    Analyze text for PII, toxicity, and prompt injection.
    
    Returns a decision (allow/warn/redact/block) with detailed detections.
    """
    if restrictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )
    
    # Build config from request
    config = PolicyConfig(
        detect_pii=request.detect_pii,
        detect_toxicity=request.detect_toxicity,
        detect_prompt_injection=request.detect_prompt_injection,
        toxicity_threshold=request.toxicity_threshold,
        pii_confidence_threshold=request.pii_confidence_threshold,
        blocked_terms=request.blocked_terms,
    )
    
    # Create restrictor with custom config
    custom_restrictor = Restrictor(config=config)
    
    # Analyze
    decision = custom_restrictor.analyze(request.text)
    
    # Convert to response
    return AnalyzeResponse(
        action=decision.action.value,
        request_id=decision.request_id,
        processing_time_ms=decision.processing_time_ms,
        summary={
            "categories_found": [c.value for c in decision.categories_found],
            "max_severity": decision.max_severity.value if decision.max_severity else None,
            "max_confidence": decision.max_confidence,
            "detection_count": len(decision.detections),
        },
        detections=[
            DetectionItem(
                category=d.category.value,
                severity=d.severity.value,
                confidence=d.confidence,
                matched_text=d.matched_text,
                position={"start": d.start_pos, "end": d.end_pos},
                explanation=d.explanation,
                detector=d.detector,
            )
            for d in decision.detections
        ],
        redacted_text=decision.redacted_text,
    )


@app.post("/analyze/batch", tags=["Analysis"])
async def analyze_batch(request: BatchAnalyzeRequest):
    """
    Analyze multiple texts in a single request.
    
    Limited to 100 texts per request.
    """
    if restrictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )
    
    config = PolicyConfig(
        detect_pii=request.detect_pii,
        detect_toxicity=request.detect_toxicity,
        detect_prompt_injection=request.detect_prompt_injection,
    )
    
    custom_restrictor = Restrictor(config=config)
    
    results = []
    for text in request.texts:
        decision = custom_restrictor.analyze(text)
        results.append({
            "action": decision.action.value,
            "request_id": decision.request_id,
            "categories_found": [c.value for c in decision.categories_found],
            "redacted_text": decision.redacted_text,
        })
    
    return {"results": results, "count": len(results)}


@app.get("/categories", tags=["Reference"])
async def list_categories():
    """
    List all detection categories.
    
    Useful for building UIs and understanding what the API detects.
    """
    return {
        "pii": [
            {"id": "pii_email", "name": "Email Address"},
            {"id": "pii_phone", "name": "Phone Number"},
            {"id": "pii_credit_card", "name": "Credit Card"},
            {"id": "pii_ssn", "name": "Social Security Number"},
            {"id": "pii_aadhaar", "name": "Aadhaar Number (India)"},
            {"id": "pii_pan", "name": "PAN Card (India)"},
            {"id": "pii_passport", "name": "Passport Number"},
            {"id": "pii_ip_address", "name": "IP Address"},
            {"id": "pii_api_key", "name": "API Key / Secret"},
            {"id": "pii_password", "name": "Password"},
        ],
        "toxicity": [
            {"id": "toxic_hate", "name": "Hate Speech"},
            {"id": "toxic_harassment", "name": "Harassment"},
            {"id": "toxic_violence", "name": "Violence / Threats"},
            {"id": "toxic_sexual", "name": "Sexual Content"},
            {"id": "toxic_self_harm", "name": "Self Harm"},
            {"id": "toxic_profanity", "name": "Profanity"},
        ],
        "security": [
            {"id": "prompt_injection", "name": "Prompt Injection"},
            {"id": "jailbreak_attempt", "name": "Jailbreak Attempt"},
            {"id": "data_exfiltration", "name": "Data Exfiltration"},
        ],
    }


# ==============================================================================
# Error Handlers
# ==============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "type": str(type(exc).__name__)},
    )
