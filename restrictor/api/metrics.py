"""
Prometheus metrics for Universal Restrictor.

Exposes metrics at /metrics endpoint.
"""

import time
from functools import wraps
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY
)

# =============================================================================
# Request Metrics
# =============================================================================

REQUEST_COUNT = Counter(
    'restrictor_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status']
)

REQUEST_LATENCY = Histogram(
    'restrictor_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# =============================================================================
# Detection Metrics
# =============================================================================

DETECTION_COUNT = Counter(
    'restrictor_detections_total',
    'Total detections by category',
    ['category', 'action']
)

ACTION_COUNT = Counter(
    'restrictor_actions_total',
    'Total actions taken',
    ['action']
)

ESCALATION_COUNT = Counter(
    'restrictor_escalations_total',
    'Requests escalated to Claude API'
)

# =============================================================================
# Claude API Metrics
# =============================================================================

CLAUDE_REQUESTS = Counter(
    'restrictor_claude_requests_total',
    'Total Claude API requests',
    ['status']  # success, error, rate_limited
)

CLAUDE_TOKENS = Counter(
    'restrictor_claude_tokens_total',
    'Total Claude API tokens',
    ['type']  # input, output
)

CLAUDE_COST = Counter(
    'restrictor_claude_cost_usd_total',
    'Total Claude API cost in USD'
)

CLAUDE_LATENCY = Histogram(
    'restrictor_claude_latency_seconds',
    'Claude API latency in seconds',
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# =============================================================================
# Rate Limiting Metrics
# =============================================================================

RATE_LIMIT_HITS = Counter(
    'restrictor_rate_limit_hits_total',
    'Total rate limit hits',
    ['limit_type']  # api_key, claude_api
)

# =============================================================================
# Feedback Metrics
# =============================================================================

FEEDBACK_COUNT = Counter(
    'restrictor_feedback_total',
    'Total feedback submissions',
    ['type', 'status']  # type: correct/false_positive/etc, status: pending/approved/rejected
)

# =============================================================================
# System Metrics
# =============================================================================

ACTIVE_REQUESTS = Gauge(
    'restrictor_active_requests',
    'Currently processing requests'
)

APP_INFO = Info(
    'restrictor',
    'Application information'
)

# Set app info
APP_INFO.info({
    'version': '0.1.0',
    'name': 'universal-restrictor'
})

# =============================================================================
# Helper Functions
# =============================================================================

def record_request(endpoint: str, method: str, status: int, duration: float):
    """Record request metrics."""
    REQUEST_COUNT.labels(endpoint=endpoint, method=method, status=status).inc()
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)


def record_detection(category: str, action: str):
    """Record detection metrics."""
    DETECTION_COUNT.labels(category=category, action=action).inc()
    ACTION_COUNT.labels(action=action).inc()


def record_claude_call(
    success: bool,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_usd: float = 0,
    latency: float = 0,
    rate_limited: bool = False
):
    """Record Claude API metrics."""
    if rate_limited:
        CLAUDE_REQUESTS.labels(status='rate_limited').inc()
        RATE_LIMIT_HITS.labels(limit_type='claude_api').inc()
    elif success:
        CLAUDE_REQUESTS.labels(status='success').inc()
        CLAUDE_TOKENS.labels(type='input').inc(input_tokens)
        CLAUDE_TOKENS.labels(type='output').inc(output_tokens)
        CLAUDE_COST.inc(cost_usd)
        CLAUDE_LATENCY.observe(latency)
    else:
        CLAUDE_REQUESTS.labels(status='error').inc()


def record_escalation():
    """Record escalation to Claude."""
    ESCALATION_COUNT.inc()


def record_rate_limit(limit_type: str = 'api_key'):
    """Record rate limit hit."""
    RATE_LIMIT_HITS.labels(limit_type=limit_type).inc()


def record_feedback(feedback_type: str, status: str = 'pending'):
    """Record feedback submission."""
    FEEDBACK_COUNT.labels(type=feedback_type, status=status).inc()


def get_metrics():
    """Generate metrics output."""
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
