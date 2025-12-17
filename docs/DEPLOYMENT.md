# Deployment Guide

## Local Development
```bash
# Prerequisites
- Python 3.10+
- Redis (optional)

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
./run.sh
```

## Docker
```bash
# Build
docker build -t universal-restrictor .

# Run
docker run -p 8000:8000 \
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

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection URL |
| `API_KEYS` | No | Built-in test keys | Comma-separated valid API keys |
| `RATE_LIMIT` | No | `60` | Requests per minute |
| `LOG_LEVEL` | No | `INFO` | Logging level |

## Health Checks
```bash
# Liveness
curl http://localhost:8000/health

# Readiness (same endpoint)
curl http://localhost:8000/health
```

## Production Checklist

- [ ] Replace test API keys with secure keys
- [ ] Configure Redis with persistence
- [ ] Set up TLS/HTTPS
- [ ] Configure proper CORS origins
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log aggregation
- [ ] Set up alerting for errors
- [ ] Load test with expected traffic
