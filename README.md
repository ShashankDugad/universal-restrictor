# Universal Restrictor

**Model-agnostic content classification API for LLM safety.**

Enterprise-grade detection for PII, toxicity, prompt injection, and finance compliance — designed for Indian financial services with on-premise deployment support.

## Features

| Detector | Description | Status |
|----------|-------------|--------|
| **PII Detection** | Email, phone, Aadhaar, PAN, bank accounts, IFSC, UPI, Demat, GST | ✅ |
| **Toxicity Detection** | Hybrid: Keywords + Escalation Classifier + Claude API | ✅ |
| **Finance Intent** | Trading signals, insider info, investment advice | ✅ |
| **Prompt Injection** | Jailbreak attempts, instruction override, system markers | ✅ |

## Security Features

| Feature | Description |
|---------|-------------|
| **API Key Auth** | Environment-based keys, no hardcoded secrets |
| **Rate Limiting** | Redis-based, works across instances |
| **CORS** | Restricted to allowed origins |
| **PII Masking** | Responses show `jo************om` not full PII |
| **Audit Logging** | JSON structured logs, no raw PII stored |
| **Input Sanitization** | Removes injection patterns before LLM calls |
| **Error Sanitization** | No internal details leaked |

## Detection Pipeline
```
Input Text
    │
    ├─→ [Auth Check] ─────────────→ 401/403 if invalid
    ├─→ [Rate Limit] ─────────────→ 429 if exceeded
    │
    ├─→ [PII Regex] ──────────────→ REDACT (fast, <5ms)
    ├─→ [Finance Regex] ──────────→ WARN/BLOCK (fast, <5ms)
    ├─→ [Prompt Injection] ───────→ BLOCK (fast, <5ms)
    │
    └─→ [Toxicity]
         ├─→ [Keywords] ──────────→ BLOCK obvious threats
         └─→ [Escalation Classifier] → Suspicious?
              ├─→ No  → ALLOW
              └─→ Yes → [Sanitize] → [Claude API] → BLOCK/ALLOW
```

**Cost:** ~$0.002 per 100 requests (only escalated cases hit Claude API)

## Quick Start
```bash
# Clone
git clone https://github.com/ShashankDugad/universal-restrictor.git
cd universal-restrictor

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure (copy and edit)
cp .env.example .env
# Edit .env with your API keys

# Run
./run.sh
```

API available at: http://localhost:8000/docs

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_KEYS` | **Yes** | - | API keys (format: `key1:tenant1:tier1,key2:tenant2:tier2`) |
| `ANTHROPIC_API_KEY` | No | - | Claude API for premium detection |
| `CORS_ORIGINS` | No | - | Allowed origins (comma-separated) |
| `REDIS_URL` | No | - | Redis for rate limiting & storage |
| `RATE_LIMIT` | No | `60` | Requests per minute |
| `AUDIT_LOG_FILE` | No | - | Path for JSON audit log file |
| `LOG_FORMAT` | No | `text` | `text` or `json` |
| `ENABLE_DOCS` | No | `true` | Enable Swagger UI |

### Example .env
```bash
API_KEYS=sk-prod-abc123xyz789defg:acme-corp:pro,sk-test-123456789abcdef:demo:free
ANTHROPIC_API_KEY=sk-ant-xxx
CORS_ORIGINS=https://app.example.com,https://admin.example.com
REDIS_URL=redis://localhost:6379/0
RATE_LIMIT=60
AUDIT_LOG_FILE=data/audit.log
```

## API Usage

### Authentication

All endpoints (except `/health`) require API key:
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/analyze ...
```

### Analyze Text
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"text": "Contact me at john@example.com"}'
```

**Response:**
```json
{
  "action": "redact",
  "request_id": "uuid",
  "processing_time_ms": 2.5,
  "summary": {
    "categories_found": ["pii_email"],
    "max_severity": "medium",
    "max_confidence": 0.95,
    "detection_count": 1
  },
  "detections": [{
    "category": "pii_email",
    "matched_text": "jo************om",
    "explanation": "Email address detected"
  }],
  "redacted_text": "Contact me at [REDACTED]"
}
```

### Response Headers
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 60
```

### Actions

| Action | Description |
|--------|-------------|
| `allow` | Safe content |
| `allow_with_warning` | Potential concern (e.g., trading intent) |
| `redact` | PII detected, redacted version provided |
| `block` | Dangerous content blocked |

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Health check |
| POST | `/analyze` | Yes | Analyze single text |
| POST | `/analyze/batch` | Yes | Analyze up to 100 texts |
| POST | `/feedback` | Yes | Submit feedback |
| GET | `/feedback/stats` | Yes | Get feedback statistics |
| GET | `/categories` | Yes | List detection categories |
| GET | `/usage` | Yes | Claude API usage stats |

## Python SDK
```python
from restrictor import Restrictor, PolicyConfig

# Basic usage
r = Restrictor()
result = r.analyze("Contact me at john@example.com")
print(result.action)        # Action.REDACT
print(result.redacted_text) # "Contact me at [REDACTED]"

# Custom policy
policy = PolicyConfig(
    detect_pii=True,
    detect_toxicity=True,
    detect_prompt_injection=True,
    detect_finance_intent=True,
    toxicity_threshold=0.7,
    pii_confidence_threshold=0.9,
    redact_replacement="[HIDDEN]",
)
r = Restrictor(policy=policy)

# Local-only mode (no Claude API)
r = Restrictor(enable_claude=False)

# Check Claude API usage
print(r.get_api_usage())
```

## India-Specific PII

| Pattern | Example | Category |
|---------|---------|----------|
| Aadhaar | `2345 6789 0123` | `pii_aadhaar` |
| PAN | `ABCDE1234F` | `pii_pan` |
| Bank Account | `50100123456789` | `pii_bank_account` |
| IFSC | `SBIN0001234` | `pii_ifsc` |
| UPI ID | `name@okaxis` | `pii_upi` |
| Demat | `IN12345678901234` | `pii_demat` |
| GST | `27AAPFU0939F1ZV` | `pii_gst` |

## Finance Intent Detection

| Category | Example | Action |
|----------|---------|--------|
| Trading Intent | "Buy RELIANCE target 2600" | `allow_with_warning` |
| Insider Info | "Source told me merger coming" | `block` |
| Investment Advice | "Guaranteed 50% returns" | `allow_with_warning` |

## Subtle Threat Detection

The escalation classifier + Claude API catches veiled threats:

| Text | Detection |
|------|-----------|
| "Something bad might happen to you" | ✅ Violence |
| "Those people are ruining our country" | ✅ Hate speech |
| "Nobody would miss me" | ✅ Self-harm |
| "I hate you" | ✅ Harassment |

## Audit Logging

JSON structured logs for compliance:
```json
{
  "timestamp": "2025-12-17T18:43:55.631559Z",
  "event_type": "api_request",
  "request_id": "e2b39097-a80b-4e60-944c-02f4a359829e",
  "tenant_id": "acme-corp",
  "input_hash": "41dba1879a951cd1b974ba852311dff...",
  "input_length": 10,
  "action": "block",
  "categories": ["toxic_harassment"],
  "confidence": 0.95,
  "processing_time_ms": 2118.89,
  "detectors_used": ["claude_haiku"]
}
```

**No raw PII stored** - only hash and length.

## Rate Limiting

- **Redis-based** - works across multiple instances
- **Default**: 60 requests/minute per API key
- **Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- **Fallback**: In-memory rate limiting if Redis unavailable

## Input Sanitization

Defense-in-depth for Claude API calls:

| Pattern | Action |
|---------|--------|
| `<\|system\|>`, `[INST]` | Replaced with `[SYS]`, `[INST_REMOVED]` |
| "Ignore all previous instructions" | Replaced with `[BLOCKED]` |
| "Pretend to be" | Replaced with `[BLOCKED]` |
| Null bytes, zero-width chars | Removed |

## Docker
```bash
# Build
docker build -t universal-restrictor .

# Run
docker run -p 8000:8000 \
  -e API_KEYS="key:tenant:tier" \
  -e ANTHROPIC_API_KEY="sk-ant-xxx" \
  -e REDIS_URL="redis://host.docker.internal:6379/0" \
  universal-restrictor
```

## Accuracy

| Test Suite | Accuracy |
|------------|----------|
| Original 100 sentences | 100% |
| Subtle threats (25 sentences) | 100% |
| Injection attempts | 100% blocked |

## Development
```bash
# Run tests
pytest tests/

# Run server with hot reload
uvicorn restrictor.api.server:app --reload

# Check audit log
cat data/audit.log | jq .
```

## Roadmap

- [x] PII detection (India-specific)
- [x] Toxicity detection (hybrid)
- [x] Finance intent detection
- [x] Prompt injection detection
- [x] Claude API premium tier
- [x] Rate limiting (Redis)
- [x] Structured audit logging
- [x] Input sanitization
- [x] API key authentication
- [x] PII masking in responses
- [ ] Kubernetes Helm chart
- [ ] Admin dashboard
- [ ] Hindi/Tamil/Telugu toxicity
- [ ] Prometheus metrics

## License

Proprietary - All rights reserved.

## Contact

Shashank Dugad - [GitHub](https://github.com/ShashankDugad)
