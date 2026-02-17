# Deployment Guide

## Local Development

### Prerequisites
- Python 3.10+
- Redis (optional, for rate limiting)
- Anthropic API key (optional, for premium detection)

### Setup
```bash
# Clone
git clone https://github.com/ShashankDugad/universal-restrictor.git
cd universal-restrictor

# Virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your settings

# Run
./run.sh
```

### Minimal .env for Development
```bash
# Required
API_KEYS=sk-dev-1234567890abcdef12345678:local-dev:pro

# Optional (enables premium detection)
ANTHROPIC_API_KEY=sk-ant-xxx

# Optional (enables Redis rate limiting)
REDIS_URL=redis://localhost:6379/0
```

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_KEYS` | **Yes** | - | Comma-separated `key:tenant:tier` |
| `ANTHROPIC_API_KEY` | No | - | Claude API key for premium detection |
| `REDIS_URL` | No | - | Redis URL for rate limiting & storage |
| `CORS_ORIGINS` | No | - | Allowed origins (comma-separated) |
| `RATE_LIMIT` | No | `60` | Requests per minute per API key |
| `AUDIT_LOG_FILE` | No | - | Path for JSON audit log |
| `LOG_FORMAT` | No | `text` | `text` or `json` |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `ENABLE_DOCS` | No | `true` | Enable Swagger UI at /docs |

### API Key Format
```
key:tenant_id:tier
```

- **key**: Minimum 16 characters (e.g., `sk-prod-abc123xyz789`)
- **tenant_id**: Identifier for the customer (e.g., `acme-corp`)
- **tier**: `free`, `pro`, or `enterprise`

Multiple keys separated by commas:
```
API_KEYS=sk-prod-key1:acme:pro,sk-prod-key2:beta:free
```

## Docker

### Build
```bash
docker build -t universal-restrictor .
```

### Run
```bash
# Minimal (local detection only)
docker run -p 8000:8000 \
  -e API_KEYS="sk-dev-1234567890abcdef12345678:dev:pro" \
  universal-restrictor

# Full (with Claude + Redis)
docker run -p 8000:8000 \
  -e API_KEYS="sk-prod-key:tenant:pro" \
  -e ANTHROPIC_API_KEY="sk-ant-xxx" \
  -e REDIS_URL="redis://host.docker.internal:6379/0" \
  -e CORS_ORIGINS="https://app.example.com" \
  -e AUDIT_LOG_FILE="/data/audit.log" \
  -v $(pwd)/data:/data \
  universal-restrictor
```

### Docker Compose
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_KEYS=${API_KEYS}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - REDIS_URL=redis://redis:6379/0
      - CORS_ORIGINS=${CORS_ORIGINS}
      - AUDIT_LOG_FILE=/data/audit.log
      - LOG_FORMAT=json
    volumes:
      - ./data:/data
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped

volumes:
  redis_data:
```

Run with:
```bash
docker-compose up -d
```

## Detection Modes

### Full Mode (Claude + Local)
```python
# Auto-enabled if ANTHROPIC_API_KEY is set
r = Restrictor()
```

Features:
- ✅ All local detectors
- ✅ Claude API for subtle threats
- ✅ Highest accuracy

### Local-Only Mode
```python
r = Restrictor(enable_claude=False)
```

Or don't set `ANTHROPIC_API_KEY`.

Features:
- ✅ PII detection (full)
- ✅ Finance intent (full)
- ✅ Prompt injection (full)
- ✅ Obvious toxicity (keywords)
- ⚠️ Subtle threats (reduced accuracy)

## Health Checks

### Endpoint
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-12-17T18:00:00Z"
}
```

### Docker Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

### Kubernetes Probes
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

## Rate Limiting

### Configuration
```bash
# Requests per minute per API key
RATE_LIMIT=60
```

### Headers

Every response includes:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 60
```

### Redis vs In-Memory

| Feature | Redis | In-Memory |
|---------|-------|-----------|
| Multi-instance | ✅ | ❌ |
| Persistence | ✅ | ❌ |
| Failover | Graceful | N/A |

If Redis is unavailable, falls back to in-memory automatically.

## Audit Logging

### Enable File Logging
```bash
AUDIT_LOG_FILE=data/audit.log
```

### Log Format
```json
{
  "timestamp": "2025-12-17T18:43:55.631559Z",
  "level": "INFO",
  "logger": "audit",
  "event_type": "api_request",
  "request_id": "uuid",
  "tenant_id": "acme-corp",
  "input_hash": "sha256...",
  "input_length": 50,
  "action": "block",
  "categories": ["toxic_harassment"],
  "confidence": 0.95,
  "processing_time_ms": 500.0,
  "detectors_used": ["claude_haiku"]
}
```

### Log Aggregation

Compatible with:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk
- Datadog
- CloudWatch Logs

## Claude API Cost Control

### Configuration

In code:
```python
from restrictor.detectors.claude_detector import RateLimitConfig

config = RateLimitConfig(
    requests_per_minute=30,      # Max Claude calls/min
    daily_cost_cap_usd=1.0,      # Daily spending limit
    max_tokens_per_request=300,  # Token limit per call
)
```

### Monitoring Usage
```bash
curl -H "X-API-Key: your-key" http://localhost:8000/usage
```

Response:
```json
{
  "total_requests": 150,
  "blocked_requests": 5,
  "input_tokens": 45000,
  "output_tokens": 3000,
  "total_cost_usd": 0.015,
  "daily_cost_usd": 0.015,
  "daily_cap_usd": 1.0,
  "remaining_daily_budget": 0.985
}
```

## Production Checklist

### Security
- [ ] Set strong `API_KEYS` (min 32 chars recommended)
- [ ] Set `ANTHROPIC_API_KEY` in secrets manager
- [ ] Configure `CORS_ORIGINS` (no wildcards)
- [ ] Enable TLS/HTTPS (via load balancer)
- [ ] Disable Swagger UI: `ENABLE_DOCS=false`
- [ ] Set `LOG_FORMAT=json` for log aggregation

### Performance
- [ ] Configure Redis for rate limiting
- [ ] Set appropriate `RATE_LIMIT`
- [ ] Monitor Claude API costs
- [ ] Set up health check monitoring

### Compliance
- [ ] Enable `AUDIT_LOG_FILE`
- [ ] Configure log retention
- [ ] Set up log forwarding
- [ ] Document data handling

### Monitoring
- [ ] Set up alerting for:
  - [ ] Error rate > 1%
  - [ ] Rate limit hits > 10/min
  - [ ] Claude API cost > 80% of cap
  - [ ] Response time > 2s
- [ ] Monitor disk space for audit logs

## On-Premise Deployment

For banks and enterprises requiring no external API calls:
```bash
# Don't set ANTHROPIC_API_KEY
# Or explicitly disable:
```
```python
r = Restrictor(enable_claude=False)
```

### Air-Gapped Environment

1. Pre-download Llama Guard model
2. Copy to server
3. Set model path in config
4. No internet required for operation

## Troubleshooting

### API returns 401
```
{"error": "authentication_required", "message": "API key required"}
```

**Fix**: Add `X-API-Key` header with valid key.

### API returns 403
```
{"error": "invalid_api_key", "message": "Invalid API key"}
```

**Fix**: Check `API_KEYS` env var format: `key:tenant:tier`

### API returns 429
```
{"error": "rate_limit_exceeded", "retry_after_seconds": 60}
```

**Fix**: Wait 60 seconds or increase `RATE_LIMIT`.

### Claude not detecting subtle threats

**Check**: Is `ANTHROPIC_API_KEY` set?
```bash
curl http://localhost:8000/usage
# Should show total_requests > 0 if Claude is being used
```

### Redis connection failed

**Logs**: `Redis rate limiter unavailable`

**Impact**: Falls back to in-memory rate limiting (single instance only).

**Fix**: Check `REDIS_URL` and Redis server status.
