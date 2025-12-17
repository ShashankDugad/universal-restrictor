# Architecture Overview

## Detection Pipeline
```
Input Text
    │
    ├─→ [PII Regex] ──────────────→ REDACT (fast, <5ms)
    ├─→ [Finance Regex] ──────────→ WARN/BLOCK (fast, <5ms)
    ├─→ [Prompt Injection] ───────→ BLOCK (fast, <5ms)
    │
    └─→ [Toxicity]
         │
         ├─→ [Keywords] ──────────→ BLOCK obvious threats (<5ms)
         │
         └─→ No keyword hit?
              │
              └─→ [Escalation Classifier] ─→ Suspicious?
                   │                              │
                   │ No                          │ Yes
                   ↓                              ↓
                 ALLOW                    [Claude API] (~500ms)
                                               │
                                               ↓
                                         BLOCK or ALLOW
```

## Components

### 1. API Layer (FastAPI)

- **Rate Limiting**: 60 requests/minute per API key
- **Authentication**: API key header (`X-API-Key`)
- **Endpoints**:
  - `POST /analyze` - Main detection endpoint
  - `POST /analyze/batch` - Batch processing
  - `POST /feedback` - Submit feedback
  - `GET /feedback/stats` - Feedback statistics
  - `GET /health` - Health check

### 2. Detectors

#### PII Detector (Regex)
- **Type**: Deterministic
- **Latency**: <5ms
- **Categories**: 17 PII types including India-specific
- **Cost**: Free

#### Toxicity Detector (Hybrid)
- **Layer 1 - Keywords**: Pattern matching for obvious threats
  - Latency: <5ms
  - Confidence: 0.98
- **Layer 2 - Escalation Classifier**: Heuristics for suspicious content
  - Latency: <5ms
  - 60+ patterns for veiled threats, hate speech, self-harm, grooming
- **Layer 3 - Claude API**: Premium detection for subtle threats
  - Latency: ~500ms
  - Confidence: 0.95
  - Cost: ~$0.00015 per call

#### Finance Intent Detector
- **Type**: Pattern-based
- **Latency**: <10ms
- **Categories**: Trading intent, insider info, investment advice

#### Prompt Injection Detector
- **Type**: Pattern-based
- **Latency**: <5ms
- **Categories**: Jailbreak, instruction override

### 3. Storage

#### Redis (Primary)
- Request cache (1 hour TTL)
- Feedback records (persistent)
- Stats cache (5 min TTL)

#### File (Fallback)
- JSON file storage when Redis unavailable

## Cost Analysis

| Scenario | Requests | Claude Calls | Cost |
|----------|----------|--------------|------|
| 100 requests | 100 | ~10 | $0.002 |
| 1,000/day | 1,000 | ~100 | $0.02 |
| 10,000/day | 10,000 | ~1,000 | $0.15 |

**Daily cap**: Configurable (default $1.00)

## Rate Limiting

### API Rate Limits
- 60 requests/minute per API key (configurable)
- Returns 429 when exceeded

### Claude API Rate Limits
- 30 requests/minute (configurable)
- $1/day cost cap (configurable)
- Automatic fallback when limits hit

## Security

- No raw user input stored (only hashes)
- API key authentication
- Rate limiting
- CORS configured
- Local-only mode available (`enable_claude=False`)

## Scaling

- **Horizontal**: Add more API pods
- **Vertical**: Increase pod resources
- **Claude API**: Auto-scales, pay-per-use
- **Redis**: Can use Redis Cluster for scale
