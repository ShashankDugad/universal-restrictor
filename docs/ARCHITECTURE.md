# Architecture Overview

## System Design
```
                    ┌──────────────┐
                    │   Client     │
                    │  (Bank App)  │
                    └──────┬───────┘
                           │ HTTPS
                           ▼
                    ┌──────────────┐
                    │   API GW /   │
                    │ Load Balancer│
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
   ┌──────────┐     ┌──────────┐     ┌──────────┐
   │ Restrictor│     │ Restrictor│     │ Restrictor│
   │  Pod 1   │     │  Pod 2   │     │  Pod N   │
   └────┬─────┘     └────┬─────┘     └────┬─────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │    Redis     │
                  │  (Feedback)  │
                  └──────────────┘
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
  - `GET /categories` - List all categories

### 2. Detectors

#### PII Detector (Regex)
- **Type**: Deterministic
- **Latency**: <5ms
- **Categories**: 17 PII types including India-specific

#### Toxicity Detector (Hybrid)
- **Type**: Keywords (fast) + Llama Guard 3 (accurate)
- **Latency**: 5-500ms depending on fallback
- **Strategy**: Keywords catch obvious threats, LLM handles nuance

#### Finance Intent Detector
- **Type**: Pattern-based
- **Latency**: <10ms
- **Categories**: Trading intent, insider info, investment advice, loan discussion

#### Prompt Injection Detector
- **Type**: Pattern-based
- **Latency**: <5ms
- **Categories**: Jailbreak, instruction override

### 3. Storage

#### Redis (Primary)
- Request cache (1 hour TTL)
- Feedback records (persistent)
- Stats cache (5 min TTL)
- Indexes for fast lookup

#### File (Fallback)
- JSON file storage
- Used when Redis unavailable
- In-memory request cache

## Data Flow
```
Request → Rate Limit Check → Auth Check → Detectors → Decision → Response
                                              ↓
                                         Cache Request
                                              ↓
                                    (Later) Feedback → Redis
```

## Security

- No raw user input stored (only hashes)
- API key authentication
- Rate limiting
- CORS configured
- No external API calls (on-prem safe)

## Scaling

- Horizontal: Add more pods
- Vertical: Increase pod resources
- Llama Guard: GPU recommended for production
- Redis: Can use Redis Cluster for scale
