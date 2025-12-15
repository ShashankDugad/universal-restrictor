# Universal Restrictor

Model-agnostic content classification for LLM applications.

**Detects:**
- 🔒 **PII** (emails, phones, credit cards, Aadhaar, PAN, API keys, passwords)
- ☠️ **Toxic content** (hate speech, harassment, violence, profanity)
- 🛡️ **Prompt injection** (jailbreaks, instruction override, data exfiltration)

**Returns:**
- `ALLOW` - Content is safe
- `ALLOW_WITH_WARNING` - Minor issues detected, logged for audit
- `REDACT` - PII removed, content allowed
- `BLOCK` - Content not allowed

## Quick Start

```bash
pip install universal-restrictor
```

```python
from restrictor import Restrictor, Action

# Initialize
r = Restrictor()

# Analyze content
decision = r.analyze("Contact me at john@example.com or call 9876543210")

print(decision.action)  # Action.REDACT
print(decision.redacted_text)  # "Contact me at [REDACTED] or call [REDACTED]"

# Check for blocks
if decision.action == Action.BLOCK:
    print("Content blocked!")
    print(f"Reason: {decision.detections[0].explanation}")
```

## Features

### PII Detection

Detects international and India-specific PII:

| Type | Examples |
|------|----------|
| Email | `john@example.com` |
| Phone | `+1-555-123-4567`, `9876543210` (Indian) |
| Credit Card | `4111-1111-1111-1111` |
| Aadhaar | `1234-5678-9012` |
| PAN | `ABCDE1234F` |
| API Keys | `sk-...`, `AKIA...`, `ghp_...` |
| Passwords | `password=secret123` |

### Toxicity Detection

Uses ML model (or keyword fallback) to detect:
- Hate speech
- Harassment
- Violence/threats
- Sexual content
- Self-harm references
- Profanity

### Prompt Injection Detection

Catches common attack patterns:
- Instruction override ("ignore previous instructions")
- Jailbreak attempts (DAN, roleplay-based)
- System prompt extraction
- Data exfiltration attempts
- Encoded payloads

## Configuration

```python
from restrictor import Restrictor, PolicyConfig, Action, Category

config = PolicyConfig(
    # What to detect
    detect_pii=True,
    detect_toxicity=True,
    detect_prompt_injection=True,
    
    # Thresholds
    toxicity_threshold=0.7,
    pii_confidence_threshold=0.8,
    
    # Actions
    pii_action=Action.REDACT,
    toxicity_action=Action.BLOCK,
    prompt_injection_action=Action.BLOCK,
    
    # Only detect specific PII types
    pii_types=[Category.PII_EMAIL, Category.PII_CREDIT_CARD],
    
    # Custom blocked terms
    blocked_terms=["competitor_name", "internal_project"],
    
    # Redaction style
    redact_replacement="[REDACTED]",
)

r = Restrictor(config=config)
```

## Audit Logging

Every decision includes audit-friendly data:

```python
decision = r.analyze("some text")

print(decision.to_dict())
# {
#     "action": "allow",
#     "request_id": "550e8400-e29b-41d4-a716-446655440000",
#     "timestamp": "2024-01-15T10:30:00.000000",
#     "processing_time_ms": 12.5,
#     "input_hash": "sha256:...",  # For audit without storing content
#     "summary": {
#         "categories_found": ["pii_email"],
#         "max_severity": "medium",
#         "max_confidence": 0.95,
#         "detection_count": 1
#     },
#     "detections": [...]
# }
```

## Installation Options

```bash
# Core only (regex-based, no ML)
pip install universal-restrictor

# With ML models (requires ~500MB download)
pip install universal-restrictor[ml]

# With API server
pip install universal-restrictor[api]

# Everything
pip install universal-restrictor[all]
```

## Performance

| Mode | Latency (p50) | Memory |
|------|---------------|--------|
| Regex only | <5ms | ~50MB |
| With ML (CPU) | ~50ms | ~500MB |
| With ML (GPU) | ~10ms | ~2GB |

## Use Cases

### 1. Pre-LLM Filter (Input)
```python
user_input = request.get("prompt")
decision = restrictor.analyze(user_input)

if decision.action == Action.BLOCK:
    return {"error": "Content policy violation"}

# Safe to send to LLM
response = llm.generate(user_input)
```

### 2. Post-LLM Filter (Output)
```python
response = llm.generate(prompt)
decision = restrictor.analyze(response)

if decision.action == Action.REDACT:
    return {"response": decision.redacted_text}
```

### 3. Audit Trail
```python
decision = restrictor.analyze(content)

# Log for compliance (no raw content stored)
audit_log.write({
    "request_id": decision.request_id,
    "input_hash": decision.input_hash,
    "action": decision.action.value,
    "categories": [c.value for c in decision.categories_found],
    "timestamp": decision.timestamp.isoformat(),
})
```

## Roadmap

- [ ] Hindi/Tamil/Telugu toxicity detection
- [ ] ML-based PII detection (names, addresses)
- [ ] Custom model fine-tuning
- [ ] Async API
- [ ] OpenTelemetry integration
- [ ] Kubernetes Helm chart

## License

MIT

## Contributing

PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).
