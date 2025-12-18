# Universal Restrictor

**Model-agnostic content classification API for LLM safety.**

Production-ready detection for PII, toxicity, prompt injection, and finance compliance — designed for Indian financial services with on-premise deployment support.

## Features

| Detector | Description | Status |
|----------|-------------|--------|
| **PII Detection** | Email, phone, Aadhaar, PAN, bank accounts, IFSC, UPI, Demat, GST | ✅ |
| **Toxicity Detection** | Hybrid: Keywords + Escalation Classifier + Claude API | ✅ |
| **Finance Intent** | Trading signals, insider info, investment advice | ✅ |
| **Prompt Injection** | Jailbreak attempts, instruction override, system markers | ✅ |
| **Active Learning** | Auto-learns patterns from approved feedback | ✅ |

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

## Quick Start
```bash
# Clone
git clone https://github.com/ShashankDugad/universal-restrictor.git
cd universal-restrictor

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run API
./run.sh

# Run Dashboard (separate terminal)
cd dashboard && python -m http.server 3000
open http://localhost:3000/standalone.html
```

## Admin Dashboard

Web-based admin interface with:

| Tab | Description |
|-----|-------------|
| **Overview** | System health, API usage, costs, feedback stats |
| **Test** | Interactive text analysis with example buttons |
| **Feedback** | Review and approve/reject user feedback |
| **Training** | Run active learning, view learned patterns |

**Access:** http://localhost:3000/standalone.html

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_KEYS` | **Yes** | - | Format: `key1:tenant1:tier1,key2:tenant2:tier2` |
| `ANTHROPIC_API_KEY` | No | - | Claude API for premium detection |
| `REDIS_URL` | No | - | Redis for rate limiting & storage |
| `CORS_ORIGINS` | No | - | Allowed origins (comma-separated) |
| `RATE_LIMIT` | No | `60` | Requests per minute |
| `AUDIT_LOG_FILE` | No | - | Path for JSON audit log |

### Example .env
```bash
API_KEYS=sk-prod-abc123xyz789:acme-corp:pro
ANTHROPIC_API_KEY=sk-ant-xxx
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=https://app.example.com
RATE_LIMIT=60
AUDIT_LOG_FILE=data/audit.log
```

## API Usage

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
    "max_confidence": 0.95
  },
  "detections": [{
    "category": "pii_email",
    "matched_text": "jo************om",
    "explanation": "Email address detected"
  }],
  "redacted_text": "Contact me at [REDACTED]"
}
```

### Actions

| Action | Description |
|--------|-------------|
| `allow` | Safe content |
| `allow_with_warning` | Potential concern |
| `redact` | PII detected, redacted |
| `block` | Dangerous content blocked |

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Health check |
| POST | `/analyze` | Yes | Analyze single text |
| POST | `/analyze/batch` | Yes | Analyze up to 100 texts |
| POST | `/feedback` | Yes | Submit feedback |
| GET | `/feedback/stats` | Yes | Feedback statistics |
| GET | `/feedback/list` | Yes | List all feedback |
| POST | `/feedback/{id}/review` | Yes | Approve/reject feedback |
| POST | `/admin/train` | Yes | Run active learning |
| GET | `/admin/learned-patterns` | Yes | List learned patterns |
| GET | `/categories` | Yes | List detection categories |
| GET | `/usage` | Yes | Claude API usage stats |

## Active Learning

The system learns from user feedback:
```
1. User submits feedback → "This was a false negative"
2. Admin reviews → Approves feedback
3. Admin runs training → Pattern extracted
4. Classifier updated → Better detection
```

### Run Training
```bash
# Via API
curl -X POST http://localhost:8000/admin/train \
  -H "X-API-Key: your-api-key"

# Via CLI
python -m restrictor.training.active_learner
```

### View Learned Patterns
```bash
curl http://localhost:8000/admin/learned-patterns \
  -H "X-API-Key: your-api-key"
```


## Monitoring (Prometheus + Grafana)

### Start Monitoring Stack
```bash
# Prometheus (metrics database)
docker run -d --name prometheus -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v $(pwd)/data/prometheus:/prometheus \
  prom/prometheus

# Grafana (dashboards)
docker run -d --name grafana -p 3001:3000 \
  -v $(pwd)/data/grafana:/var/lib/grafana \
  grafana/grafana
```

### URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Metrics endpoint | http://localhost:8000/metrics | - |
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3001 | admin/admin |

### Grafana Setup

1. Add Data Source: Connections → Prometheus → URL: `http://host.docker.internal:9090`
2. Import Dashboard: Dashboards → Import → Upload `grafana-dashboard.json`

### Available Metrics

| Metric | Description |
|--------|-------------|
| `restrictor_requests_total` | Total requests by endpoint, method, status |
| `restrictor_request_latency_seconds` | Request latency histogram |
| `restrictor_detections_total` | Detections by category and action |
| `restrictor_actions_total` | Actions taken (allow/block/redact) |
| `restrictor_claude_cost_usd_total` | Claude API cost |
| `restrictor_rate_limit_hits_total` | Rate limit hits |
| `restrictor_active_requests` | Currently processing requests |

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

## Kubernetes Deployment
```bash
# Install with Helm
helm install restrictor ./helm/universal-restrictor \
  --set secrets.apiKeys="sk-prod-key:tenant:pro" \
  --set secrets.anthropicApiKey="sk-ant-xxx"

# Port forward
kubectl port-forward svc/restrictor-universal-restrictor 8000:8000
```

## Docker
```bash
# Build
docker build -t universal-restrictor .

# Run
docker run -p 8000:8000 \
  -e API_KEYS="key:tenant:tier" \
  -e ANTHROPIC_API_KEY="sk-ant-xxx" \
  universal-restrictor
```

## Project Structure
```
universal-restrictor/
├── restrictor/
│   ├── api/
│   │   ├── server.py          # FastAPI app
│   │   ├── middleware.py      # Auth, rate limiting
│   │   └── logging_config.py  # Audit logging
│   ├── detectors/
│   │   ├── pii.py             # PII detection
│   │   ├── toxicity.py        # Toxicity detection
│   │   ├── prompt_injection.py
│   │   ├── finance_intent.py
│   │   ├── escalation_classifier.py
│   │   ├── claude_detector.py
│   │   ├── input_sanitizer.py
│   │   └── learned_patterns.json
│   ├── training/
│   │   └── active_learner.py  # Active learning
│   ├── feedback/
│   │   ├── storage.py
│   │   └── redis_storage.py
│   ├── engine.py
│   └── models.py
├── dashboard/
│   └── standalone.html        # Admin dashboard
├── helm/
│   └── universal-restrictor/  # Kubernetes Helm chart
├── docs/
│   ├── ARCHITECTURE.md
│   └── DEPLOYMENT.md
├── Dockerfile
├── .env.example
└── run.sh
```

## Accuracy

| Test Suite | Accuracy |
|------------|----------|
| Original 100 sentences | 100% |
| Subtle threats (25 sentences) | 100% |
| Injection attempts | 100% blocked |

## Roadmap

- [x] PII detection (India-specific)
- [x] Toxicity detection (hybrid)
- [x] Finance intent detection
- [x] Prompt injection detection
- [x] Claude API premium tier
- [x] Rate limiting (Redis)
- [x] Structured audit logging
- [x] Input sanitization
- [x] Admin dashboard
- [x] Feedback system
- [x] Active learning
- [x] Kubernetes Helm chart
- [ ] Hindi/Tamil/Telugu toxicity
- [ ] Prometheus metrics
- [ ] CI/CD pipeline

## License

Proprietary - All rights reserved.

## Contact

Shashank Dugad - [GitHub](https://github.com/ShashankDugad)
