# Architecture Overview

## System Design
```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Request                               │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API Gateway                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │
│  │ Auth Check  │→ │ Rate Limit  │→ │ Input Validation            │  │
│  │ (API Key)   │  │ (Redis)     │  │ (Pydantic)                  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Detection Engine                                │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Fast Path (Regex) - <5ms                                        │ │
│  │  ├── PII Detector (17 India patterns)                          │ │
│  │  ├── Finance Intent (trading, insider, advice)                 │ │
│  │  └── Prompt Injection (system markers, jailbreaks)             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Toxicity Detection (Hybrid)                                     │ │
│  │  ├── Keywords (obvious threats) ──────────────→ BLOCK          │ │
│  │  │                                                              │ │
│  │  └── Escalation Classifier                                      │ │
│  │       ├── Base patterns (70+)                                   │ │
│  │       ├── Learned patterns (from feedback) ◄── Active Learning │ │
│  │       │                                                         │ │
│  │       ├── Safe patterns ──────────────────────→ ALLOW          │ │
│  │       └── Suspicious ─┬─→ Input Sanitizer                      │ │
│  │                       └─→ Claude API ─────────→ BLOCK/ALLOW    │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Response + Feedback Loop                         │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────────────────┐│
│  │ PII Mask    │  │ Audit Log   │  │ Feedback → Review → Training  ││
│  │ in Response │  │ (JSON)      │  │              ↓                ││
│  └─────────────┘  └─────────────┘  │      Learned Patterns         ││
│                                     └───────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. API Layer (FastAPI)

| Component | Description |
|-----------|-------------|
| **Authentication** | API key from `X-API-Key` header |
| **Rate Limiting** | Redis-based sliding window |
| **CORS** | Restricted to `CORS_ORIGINS` |
| **Input Validation** | Pydantic models, max 50KB |
| **Error Handling** | Sanitized responses |

### 2. Detectors

#### PII Detector
- **Latency**: <5ms
- **Patterns**: 17 types including India-specific
- **Categories**: Email, phone, Aadhaar, PAN, bank account, IFSC, UPI, Demat, GST

#### Toxicity Detector (Hybrid)
- **Layer 1 - Keywords**: Pattern matching, <5ms
- **Layer 2 - Escalation Classifier**: 
  - 70+ base patterns
  - Learned patterns from feedback
- **Layer 3 - Claude API**: Premium detection, ~500ms

#### Finance Intent Detector
- **Latency**: <10ms
- **Categories**: Trading intent, insider info, investment advice

#### Prompt Injection Detector
- **Latency**: <5ms
- **Categories**: Instruction override, jailbreak, system markers

### 3. Active Learning
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ User Submits │ ──→ │ Admin Reviews│ ──→ │ Run Training │
│ Feedback     │     │ & Approves   │     │              │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Classifier   │ ◄── │ Load Learned │ ◄── │ Extract      │
│ Uses Patterns│     │ Patterns     │     │ Patterns     │
└──────────────┘     └──────────────┘     └──────────────┘
```

**Training Process:**
1. Extract patterns from false negative comments
2. Generate regex patterns
3. Save to `learned_patterns.json`
4. Escalation classifier loads on init

### 4. Feedback System

| Feedback Type | Action |
|---------------|--------|
| `correct` | Positive signal (confidence boost) |
| `false_positive` | We flagged incorrectly |
| `false_negative` | We missed something → Extracts patterns |
| `category_correction` | Wrong category assigned |

### 5. Admin Dashboard

| Tab | Features |
|-----|----------|
| **Overview** | Health, usage, costs, feedback stats |
| **Test** | Interactive analysis with examples |
| **Feedback** | Review, approve/reject |
| **Training** | Run training, view learned patterns |

### 6. Security Components

#### Input Sanitizer
Removes dangerous patterns before Claude API:
- System markers: `<|system|>`, `[INST]`
- Injection attempts: "ignore previous"
- Encoding tricks: base64, hex

#### Audit Logger
JSON structured logging:
```json
{
  "event_type": "api_request",
  "tenant_id": "acme-corp",
  "input_hash": "sha256...",
  "action": "block",
  "categories": ["toxic_harassment"]
}
```

### 7. Storage

| Component | Backend | Purpose |
|-----------|---------|---------|
| Rate Limiting | Redis | Sliding window counters |
| Request Cache | Redis | 1 hour TTL for feedback |
| Feedback | Redis | Feedback records |
| Learned Patterns | JSON file | Active learning output |
| Audit Log | File | Compliance logging |

## Request Flow
```
1. Request arrives with X-API-Key
2. Auth middleware validates → 401/403 if invalid
3. Rate limiter checks Redis → 429 if exceeded
4. Pydantic validates body → 400 if invalid
5. Engine runs detectors:
   a. PII regex (always)
   b. Prompt injection regex (always)
   c. Finance intent regex (always)
   d. Toxicity:
      - Keywords first
      - Escalation classifier (base + learned)
      - Claude API if escalated
6. Response built with masked PII
7. Request cached for feedback (1 hour)
8. Audit log written
9. Response returned with rate limit headers
```

## Cost Analysis

| Scenario | Requests | Claude Calls | Cost |
|----------|----------|--------------|------|
| Normal traffic | 1,000 | ~50-100 | $0.01-0.02 |
| High risk | 1,000 | ~200-300 | $0.03-0.05 |
| 10K/day | 10,000 | ~500-1,000 | $0.10-0.15 |

## Performance

| Operation | Latency |
|-----------|---------|
| PII detection | <5ms |
| Finance detection | <10ms |
| Prompt injection | <5ms |
| Toxicity (local) | <10ms |
| Toxicity (Claude) | ~500ms |
| **Average** | ~50-100ms |

## Scaling

### Horizontal
- Stateless API pods
- Redis for shared state
- Load balancer

### Caching
- Request results: 1 hour
- Stats: 5 minutes
- Rate limits: sliding window

## Security Layers
```
Layer 1: Network (CORS, TLS, Rate limiting)
Layer 2: Authentication (API keys, tenant isolation)
Layer 3: Input Validation (Pydantic, length limits)
Layer 4: Detection (Prompt injection, sanitization)
Layer 5: Output (PII masking, error sanitization)
Layer 6: Audit (Structured logging)
```
