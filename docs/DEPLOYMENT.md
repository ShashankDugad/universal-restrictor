# Deployment Guide

## Local Development
```bash
# Prerequisites
- Python 3.10+
- Redis (optional)
- Anthropic API key (optional, for premium detection)

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Environment
export ANTHROPIC_API_KEY="your-key-here"  # Optional

# Run
./run.sh
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | No | - | Claude API for premium detection |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection |
| `RATE_LIMIT` | No | `60` | API requests per minute |
| `LOG_LEVEL` | No | `INFO` | Logging level |

### Detection Modes

**Full Mode (with Claude API):**
```python
r = Restrictor()  # Auto-enables if ANTHROPIC_API_KEY set
```

**Local-Only Mode:**
```python
r = Restrictor(enable_claude=False)
```

## Docker
```bash
# Build
docker build -t universal-restrictor .

# Run (local-only)
docker run -p 8000:8000 universal-restrictor

# Run (with Claude API)
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-key \
  -e REDIS_URL=redis://host.docker.internal:6379/0 \
  universal-restrictor
```

## Docker Compose
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

## Kubernetes (Coming Soon)

Helm chart will include:
- Deployment with auto-scaling
- Service (ClusterIP/LoadBalancer)
- ConfigMap for configuration
- Secret for API keys
- Redis StatefulSet
- Ingress (optional)

## Health Checks
```bash
# Liveness & Readiness
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "detectors": {
    "pii": "active",
    "toxicity": "active",
    "prompt_injection": "active",
    "finance_intent": "active"
  }
}
```

## Cost Management

### Claude API Limits
```python
from restrictor.detectors.claude_detector import RateLimitConfig

config = RateLimitConfig(
    requests_per_minute=30,      # Max calls per minute
    daily_cost_cap_usd=1.0,      # Daily spending limit
    max_tokens_per_request=300,  # Token limit
)
```

### Monitoring Usage
```python
r = Restrictor()
# ... process requests ...

usage = r.get_api_usage()
print(f"Total cost: ${usage['total_cost_usd']}")
print(f"Remaining budget: ${usage['remaining_daily_budget']}")
```

## Production Checklist

- [ ] Set `ANTHROPIC_API_KEY` in secrets
- [ ] Configure Redis with persistence
- [ ] Set up TLS/HTTPS
- [ ] Configure CORS origins
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log aggregation
- [ ] Set up alerting for:
  - [ ] Error rates
  - [ ] Claude API cost approaching limit
  - [ ] Rate limit hits
- [ ] Load test with expected traffic
- [ ] Set appropriate rate limits

## On-Premise Deployment

For banks/enterprises requiring no external API calls:
```python
# Disable Claude API entirely
r = Restrictor(enable_claude=False)
```

Detection capabilities in local-only mode:
- ✅ PII detection (full)
- ✅ Finance intent (full)
- ✅ Prompt injection (full)
- ✅ Obvious toxicity (keywords)
- ⚠️ Subtle threats (reduced accuracy)
