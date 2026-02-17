# API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
All API requests require an `X-API-Key` header:
```
X-API-Key: your-api-key
```

---

## Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-12-22T18:06:59.900186"
}
```

---

### Analyze Text
```http
POST /analyze
```

**Request:**
```json
{
  "text": "Text to analyze",
  "policy": {
    "detect_pii": true,
    "detect_toxicity": true,
    "pii_action": "redact",
    "toxicity_action": "block"
  }
}
```

**Response:**
```json
{
  "action": "block",
  "detections": [
    {
      "category": "toxic_harassment",
      "severity": "high",
      "confidence": 0.95,
      "detector": "moe_harassment",
      "explanation": "[MOE] MoE detected harassment content",
      "matched_text": "you are worthless garbage",
      "start_pos": 0,
      "end_pos": 25
    }
  ],
  "redacted_text": null,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "latency_ms": 45
}
```

**Actions:**
| Action | Description |
|--------|-------------|
| `allow` | Content is safe |
| `warn` | Content flagged but allowed |
| `redact` | PII found and redacted |
| `block` | Content blocked |

---

### Submit Feedback
```http
POST /feedback
```

**Request:**
```json
{
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "feedback_type": "false_positive",
  "comment": "This was incorrectly flagged"
}
```

**Response:**
```json
{
  "feedback_id": "fb_abc123",
  "status": "received"
}
```

---

### Feedback Stats
```http
GET /feedback/stats
```

**Response:**
```json
{
  "total": 150,
  "by_type": {
    "false_positive": 45,
    "false_negative": 30,
    "correct": 75
  },
  "reviewed": 120,
  "pending_review": 30
}
```

---

### Metrics (Prometheus)
```http
GET /metrics
```

**Response:**
```
# HELP restrictor_requests_total Total API requests
# TYPE restrictor_requests_total counter
restrictor_requests_total{action="allow"} 150
restrictor_requests_total{action="block"} 25

# HELP restrictor_detections_total Total detections
# TYPE restrictor_detections_total counter
restrictor_detections_total{category="toxic_harassment"} 20
restrictor_detections_total{category="pii_email"} 15

# HELP restrictor_request_latency_seconds Request latency
# TYPE restrictor_request_latency_seconds histogram
restrictor_request_latency_seconds_bucket{le="0.01"} 100
restrictor_request_latency_seconds_bucket{le="0.05"} 150
restrictor_request_latency_seconds_bucket{le="0.1"} 170
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "error": "authentication_required",
  "message": "API key is required"
}
```

### 403 Forbidden
```json
{
  "error": "invalid_api_key",
  "message": "Invalid API key"
}
```

### 429 Rate Limited
```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Try again in 60 seconds."
}
```

### 500 Internal Error
```json
{
  "error": "internal_error",
  "message": "An internal error occurred"
}
```

---

## Rate Limits

| Tier | Requests/min | Requests/day |
|------|--------------|--------------|
| Free | 60 | 1,000 |
| Pro | 600 | 50,000 |
| Enterprise | 6,000 | Unlimited |
