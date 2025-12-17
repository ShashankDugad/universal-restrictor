# Universal Restrictor

**Model-agnostic content classification API for LLM safety.**

Enterprise-grade detection for PII, toxicity, prompt injection, and finance compliance — designed for Indian financial services and on-premise deployment.

## Features

| Detector | Description | Status |
|----------|-------------|--------|
| **PII Detection** | Email, phone, credit card, Aadhaar, PAN, bank accounts, IFSC, UPI, Demat, GST | ✅ |
| **Toxicity Detection** | Hybrid keyword + Llama Guard 3 (local, no API calls) | ✅ |
| **Finance Intent** | Trading signals, insider info, investment advice, loan discussions | ✅ |
| **Prompt Injection** | Jailbreak attempts, instruction override | ✅ |

## Quick Start
```bash
# Clone
git clone https://github.com/ShashankDugad/universal-restrictor.git
cd universal-restrictor

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Download Llama Guard 3 (optional, for enhanced toxicity detection)
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
| `block` | Dangerous content (toxicity, insider info, prompt injection) |

## India Finance PII (Unique)

| Pattern | Example | Category |
|---------|---------|----------|
| Bank Account | `50100123456789` | `pii_bank_account` |
| IFSC Code | `SBIN0001234` | `pii_ifsc` |
| UPI ID | `name@okaxis` | `pii_upi` |
| Demat Account | `IN12345678901234` | `pii_demat` |
| GST Number | `27AAPFU0939F1ZV` | `pii_gst` |
| Aadhaar | `2345 6789 0123` | `pii_aadhaar` |
| PAN | `ABCDE1234F` | `pii_pan` |

## Finance Intent Detection (Novel)

| Category | Example | Action |
|----------|---------|--------|
| Trading Intent | "Buy RELIANCE target 2600" | `allow_with_warning` |
| Insider Info | "Source told me merger coming" | `block` |
| Investment Advice | "Guaranteed 50% returns" | `allow_with_warning` |
| Loan Discussion | "Loan of Rs 50 lakh approved" | `allow_with_warning` |

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
│  ├── Toxicity (Hybrid: Keywords + Llama Guard 3)    │
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

- **No external API calls** - Llama Guard runs locally
- **No data leaves your network** - 100% on-prem
- **Docker ready** - `docker build -t restrictor .`
- **Kubernetes ready** - Helm chart coming soon

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `GROQ_API_KEY` | - | Optional: Groq API for cloud toxicity |

### Policy Configuration
```python
from restrictor import Restrictor, PolicyConfig

policy = PolicyConfig(
    detect_pii=True,
    detect_toxicity=True,
    detect_prompt_injection=True,
    detect_finance_intent=True,
    toxicity_threshold=0.7,
    pii_confidence_threshold=0.8,
    pii_types=["pii_email", "pii_phone"],  # Optional filter
)

r = Restrictor(policy=policy)
result = r.analyze("Your text here")
```

## Feedback Loop

Submit feedback to improve detection:
```bash
# After analyzing, submit feedback
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "uuid-from-analyze",
    "feedback_type": "false_positive",
    "comment": "This is a public email"
  }'
```

Feedback types: `correct`, `false_positive`, `false_negative`, `category_correction`

## Development
```bash
# Run tests
pytest tests/

# Run with hot reload
uvicorn restrictor.api.server:app --reload

# Docker build
docker build -t universal-restrictor .
docker run -p 8000:8000 universal-restrictor
```

## License

Proprietary - All rights reserved.

## Contact

Shashank Dugad - [GitHub](https://github.com/ShashankDugad)
