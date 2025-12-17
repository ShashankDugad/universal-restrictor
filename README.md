# Universal Restrictor

**Model-agnostic content classification API for LLM safety.**

Enterprise-grade detection for PII, toxicity, prompt injection, and finance compliance — designed for Indian financial services with on-premise deployment support.

## Features

| Detector | Description | Status |
|----------|-------------|--------|
| **PII Detection** | Email, phone, Aadhaar, PAN, bank accounts, IFSC, UPI, Demat, GST | ✅ |
| **Toxicity Detection** | Hybrid: Keywords + Llama Guard 3 + Claude API (premium) | ✅ |
| **Finance Intent** | Trading signals, insider info, investment advice | ✅ |
| **Prompt Injection** | Jailbreak attempts, instruction override | ✅ |

## Detection Pipeline
```
Input Text
    │
    ├─→ [PII Regex] ──────────────→ REDACT (fast, free)
    ├─→ [Finance Regex] ──────────→ WARN/BLOCK (fast, free)
    ├─→ [Prompt Injection] ───────→ BLOCK (fast, free)
    │
    └─→ [Toxicity]
         ├─→ [Keywords] ──────────→ BLOCK obvious threats
         │
         └─→ [Escalation Classifier]
              ├─→ Safe ───────────→ ALLOW (fast, free)
              └─→ Suspicious ─────→ [Claude API] → BLOCK/ALLOW
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

# Set API key (for premium detection)
export ANTHROPIC_API_KEY="your-key-here"

# Download Llama Guard 3 (optional, for local detection)
python -c "
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id='mradermacher/Llama-Guard-3-8B-GGUF',
    filename='Llama-Guard-3-8B.Q8_0.gguf',
    local_dir='./models'
)
"

# Run
./run.sh
```

API available at: http://localhost:8000/docs

## API Usage

### Analyze Text
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-123" \
  -d '{"text": "Contact me at john@example.com"}'
```

**Response:**
```json
{
  "action": "redact",
  "request_id": "uuid",
  "processing_time_ms": 15.2,
  "summary": {
    "categories_found": ["pii_email"],
    "max_severity": "medium",
    "max_confidence": 0.95
  },
  "detections": [...],
  "redacted_text": "Contact me at [REDACTED]"
}
```

### Actions

| Action | Description |
|--------|-------------|
| `allow` | Safe content |
| `allow_with_warning` | Potential concern (e.g., trading intent) |
| `redact` | PII detected, redacted version provided |
| `block` | Dangerous content blocked |

## Python SDK Usage
```python
from restrictor import Restrictor, PolicyConfig

# Basic usage
r = Restrictor()
result = r.analyze("Contact me at john@example.com")
print(result.action)        # Action.REDACT
print(result.redacted_text) # "Contact me at [REDACTED]"

# With custom policy
policy = PolicyConfig(
    detect_pii=True,
    detect_toxicity=True,
    detect_prompt_injection=True,
    detect_finance_intent=True,
    pii_types=["pii_email", "pii_phone"],
    pii_confidence_threshold=0.9,
    redact_replacement="[HIDDEN]",
)
r = Restrictor(policy=policy)

# Disable Claude API (local-only detection)
r = Restrictor(enable_claude=False)

# Check API usage
usage = r.get_api_usage()
print(f"Cost: ${usage['total_cost_usd']}")
```

## PolicyConfig Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `detect_pii` | bool | `True` | Enable PII detection |
| `detect_toxicity` | bool | `True` | Enable toxicity detection |
| `detect_prompt_injection` | bool | `True` | Enable prompt injection detection |
| `detect_finance_intent` | bool | `True` | Enable finance intent detection |
| `pii_types` | List[str] | `None` | Filter specific PII types (None = all) |
| `pii_confidence_threshold` | float | `0.8` | Minimum confidence for PII |
| `toxicity_threshold` | float | `0.7` | Minimum confidence for toxicity |
| `redact_replacement` | str | `"[REDACTED]"` | Custom replacement text |

## India Finance PII

| Pattern | Example | Category |
|---------|---------|----------|
| Bank Account | `50100123456789` | `pii_bank_account` |
| IFSC Code | `SBIN0001234` | `pii_ifsc` |
| UPI ID | `name@okaxis` | `pii_upi` |
| Demat Account | `IN12345678901234` | `pii_demat` |
| GST Number | `27AAPFU0939F1ZV` | `pii_gst` |
| Aadhaar | `2345 6789 0123` | `pii_aadhaar` |
| PAN | `ABCDE1234F` | `pii_pan` |

## Finance Intent Detection

| Category | Example | Action |
|----------|---------|--------|
| Trading Intent | "Buy RELIANCE target 2600" | `allow_with_warning` |
| Insider Info | "Source told me merger coming" | `block` |
| Investment Advice | "Guaranteed 50% returns" | `allow_with_warning` |

## Subtle Threat Detection (Premium)

The escalation classifier + Claude API catches veiled threats:

| Text | Detection |
|------|-----------|
| "Something bad might happen to you" | ✅ Violence |
| "Those people are ruining our country" | ✅ Hate speech |
| "Nobody would miss me" | ✅ Self-harm |
| "You're mature for your age" | ✅ Grooming |

## Rate Limiting & Cost Control
```python
from restrictor.detectors.claude_detector import ClaudeDetector, RateLimitConfig

# Custom rate limits
config = RateLimitConfig(
    requests_per_minute=30,      # Max 30 Claude calls/min
    daily_cost_cap_usd=1.0,      # $1/day max
    max_tokens_per_request=300,  # Token limit per call
)

detector = ClaudeDetector(rate_limit=config)
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | - | Claude API key (for premium detection) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |

## Architecture
```
┌─────────────────────────────────────────────────────┐
│                Universal Restrictor                  │
├─────────────────────────────────────────────────────┤
│  API (FastAPI)                                       │
│  ├── Rate Limiting (60 req/min)                     │
│  ├── API Key Auth                                   │
│  └── CORS enabled                                   │
├─────────────────────────────────────────────────────┤
│  Detectors                                          │
│  ├── PII (Regex) - India-specific patterns          │
│  ├── Toxicity (Hybrid)                              │
│  │   ├── Keywords (fast, obvious threats)           │
│  │   ├── Escalation Classifier (suspicious check)   │
│  │   └── Claude API (premium, subtle threats)       │
│  ├── Finance Intent (Pattern-based)                 │
│  └── Prompt Injection (Pattern-based)               │
├─────────────────────────────────────────────────────┤
│  Storage                                            │
│  ├── Redis (primary, persistent)                    │
│  └── File (fallback)                                │
└─────────────────────────────────────────────────────┘
```

## On-Premise Deployment

Designed for banks and financial institutions:

- **Local-only mode** - Set `enable_claude=False`
- **No data leaves your network** - Llama Guard runs locally
- **Docker ready** - `docker build -t restrictor .`
- **Kubernetes ready** - Helm chart coming soon

## Accuracy

| Test Suite | Accuracy |
|------------|----------|
| Original 100 sentences | 100% |
| Subtle threats (25 sentences) | 100% |

## Development
```bash
# Run tests
pytest tests/

# Run server with hot reload
uvicorn restrictor.api.server:app --reload

# Docker
docker build -t universal-restrictor .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=xxx universal-restrictor
```

## Roadmap

- [x] PII detection (India-specific)
- [x] Toxicity detection (hybrid)
- [x] Finance intent detection
- [x] Prompt injection detection
- [x] Claude API premium tier
- [x] Rate limiting & cost control
- [x] Redis storage
- [ ] Kubernetes Helm chart
- [ ] Admin dashboard
- [ ] Hindi/Tamil/Telugu toxicity
- [ ] ML-based PII (names, addresses)

## License

Proprietary - All rights reserved.

## Contact

Shashank Dugad - [GitHub](https://github.com/ShashankDugad)
