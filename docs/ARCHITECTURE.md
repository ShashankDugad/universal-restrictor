# Architecture Overview

## System Design
```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Request                           │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Auth Check  │→ │ Rate Limit  │→ │ Input Validation        │  │
│  │ (API Key)   │  │ (Redis)     │  │ (Pydantic)              │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Detection Engine                            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Fast Path (Regex) - <5ms                                  │   │
│  │  ├── PII Detector (17 India patterns)                    │   │
│  │  ├── Finance Intent (trading, insider, advice)           │   │
│  │  └── Prompt Injection (system markers, jailbreaks)       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Toxicity Detection (Hybrid)                               │   │
│  │  ├── Keywords (obvious threats) ──────────→ BLOCK        │   │
│  │  │                                                        │   │
│  │  └── Escalation Classifier                                │   │
│  │       ├── Safe patterns ──────────────────→ ALLOW        │   │
│  │       └── Suspicious ─┬─→ Input Sanitizer                │   │
│  │                       └─→ Claude API ─────→ BLOCK/ALLOW  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Response + Audit                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ PII Mask    │  │ Audit Log   │  │ Response Headers        │  │
│  │ in Response │  │ (JSON)      │  │ (Rate Limit)            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. API Layer (FastAPI)

| Component | Description |
|-----------|-------------|
| **Authentication** | API key from `X-API-Key` header, validated against env |
| **Rate Limiting** | Redis-based sliding window, 60 req/min default |
| **CORS** | Restricted to `CORS_ORIGINS` env var |
| **Input Validation** | Pydantic models, max 50KB text |
| **Error Handling** | Sanitized responses, no internal details |

### 2. Detectors

#### PII Detector (Regex)
- **Latency**: <5ms
- **Patterns**: 17 types including India-specific
- **Categories**: Email, phone, Aadhaar, PAN, bank account, IFSC, UPI, Demat, GST, credit card, SSN, passport, password, API key

#### Toxicity Detector (Hybrid)
- **Layer 1 - Keywords**: Pattern matching, <5ms, 0.98 confidence
- **Layer 2 - Escalation Classifier**: 70+ heuristic patterns
  - Veiled threats, hate speech, self-harm, grooming, radicalization
- **Layer 3 - Claude API**: Premium detection, ~500ms, 0.95 confidence
  - Only called for escalated (suspicious) text
  - Input sanitized before sending

#### Finance Intent Detector
- **Latency**: <10ms
- **Categories**: Trading intent, insider info, investment advice, loan discussion
- **Stocks**: 26 major Indian stocks (NIFTY, BANKNIFTY, RELIANCE, etc.)

#### Prompt Injection Detector
- **Latency**: <5ms
- **Categories**: Instruction override, DAN/jailbreak, privilege escalation, roleplay, safety bypass, system markers

### 3. Security Components

#### Input Sanitizer
Removes dangerous patterns before Claude API calls:
- System markers: `<|system|>`, `[INST]`, `<<SYS>>`
- Injection attempts: "ignore previous", "pretend to be"
- Encoding tricks: base64, hex, rot13
- Suspicious chars: null bytes, zero-width spaces

#### Audit Logger
JSON structured logging for compliance:
```json
{
  "timestamp": "2025-12-17T18:43:55Z",
  "event_type": "api_request",
  "request_id": "uuid",
  "tenant_id": "acme-corp",
  "input_hash": "sha256...",
  "input_length": 50,
  "action": "block",
  "categories": ["toxic_harassment"],
  "processing_time_ms": 500,
  "detectors_used": ["claude_haiku"]
}
```

### 4. Storage

#### Redis (Primary)
- Rate limiting (sliding window)
- Request cache (1 hour TTL)
- Feedback records
- Stats cache (5 min TTL)

#### File (Fallback)
- JSON file storage when Redis unavailable
- Audit log file (always JSON)

## Request Flow
```
1. Request arrives with X-API-Key header
2. Auth middleware validates API key → 401/403 if invalid
3. Rate limiter checks Redis → 429 if exceeded
4. Pydantic validates request body → 400 if invalid
5. Engine runs detectors in order:
   a. PII regex (always)
   b. Prompt injection regex (always)
   c. Finance intent regex (always)
   d. Toxicity (skip if PII/finance found):
      - Keywords first
      - Escalation classifier if no keywords hit
      - Claude API if escalated (after sanitization)
6. Response built with masked PII
7. Audit log written (JSON)
8. Response returned with rate limit headers
```

## Cost Analysis

| Scenario | Requests | Claude Calls | Estimated Cost |
|----------|----------|--------------|----------------|
| Normal traffic | 1,000 | ~50-100 | $0.01-0.02 |
| High risk content | 1,000 | ~200-300 | $0.03-0.05 |
| 10,000/day | 10,000 | ~500-1,000 | $0.10-0.15 |

**Daily cap**: Configurable (default $1.00)

## Performance

| Operation | Latency |
|-----------|---------|
| PII detection | <5ms |
| Finance detection | <10ms |
| Prompt injection | <5ms |
| Toxicity (keywords) | <5ms |
| Toxicity (Claude) | ~500ms |
| **Average request** | ~50-100ms |

## Security Layers
```
Layer 1: Network
├── CORS (restricted origins)
├── Rate limiting (Redis)
└── TLS (in production)

Layer 2: Authentication
├── API key validation
├── Tenant isolation
└── No hardcoded secrets

Layer 3: Input Validation
├── Pydantic models
├── Length limits
└── Format validation

Layer 4: Detection
├── Prompt injection blocking
├── Input sanitization
└── Pattern removal

Layer 5: Output
├── PII masking
├── Error sanitization
└── Audit logging
```

## Scaling

### Horizontal Scaling
- Stateless API pods
- Redis for shared state (rate limits, cache)
- Load balancer distributes traffic

### Vertical Scaling
- Increase pod resources
- Claude API auto-scales

### Caching
- Request results cached 1 hour
- Stats cached 5 minutes
- Rate limit windows in Redis

## Monitoring Points

| Metric | Description |
|--------|-------------|
| `requests_total` | Total API requests |
| `requests_blocked` | Blocked by detection |
| `rate_limit_hits` | Rate limit exceeded |
| `claude_api_calls` | Claude API usage |
| `claude_api_cost` | Claude API cost |
| `processing_time_ms` | Request latency |
| `detection_by_category` | Detections by type |
