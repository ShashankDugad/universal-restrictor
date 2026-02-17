# Architecture Overview

## System Architecture
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │   Web    │  │  Mobile  │  │   API    │  │  Webhook │                    │
│  │   App    │  │   App    │  │  Client  │  │  Handler │                    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘                    │
└───────┼─────────────┼─────────────┼─────────────┼───────────────────────────┘
        │             │             │             │
        └─────────────┴──────┬──────┴─────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         FastAPI Server                               │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │   │
│  │  │   Auth   │  │   Rate   │  │   CORS   │  │   Request        │    │   │
│  │  │Middleware│  │  Limiter │  │ Handling │  │   Validation     │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DETECTION ENGINE                                   │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        Restrictor Engine                               │  │
│  │                                                                        │  │
│  │   Input Text                                                           │  │
│  │       ↓                                                                │  │
│  │   ┌─────────────────┐                                                  │  │
│  │   │ Safe Phrase     │ → Skip if "namaste", "dhanyavaad", etc.         │  │
│  │   │ Check           │                                                  │  │
│  │   └────────┬────────┘                                                  │  │
│  │            ↓                                                           │  │
│  │   ┌─────────────────┐                                                  │  │
│  │   │ Keyword         │ → Instant match: slurs, threats, bombs          │  │
│  │   │ Detector        │   <1ms, 98% confidence                          │  │
│  │   └────────┬────────┘                                                  │  │
│  │            ↓                                                           │  │
│  │   ┌─────────────────┐                                                  │  │
│  │   │ MoE Detector    │ → 2-Stage MuRIL model                           │  │
│  │   │ (Stage 1+2)     │   ~50ms, 96% F1                                 │  │
│  │   └────────┬────────┘                                                  │  │
│  │            ↓                                                           │  │
│  │   ┌─────────────────┐                                                  │  │
│  │   │ Claude API      │ → Edge cases, low confidence                    │  │
│  │   │ Detector        │   ~1-2s, 99%+ accuracy                          │  │
│  │   └────────┬────────┘                                                  │  │
│  │            ↓                                                           │  │
│  │   ┌─────────────────┐                                                  │  │
│  │   │ PII Detector    │ → Email, Phone, Aadhaar, PAN                    │  │
│  │   │                 │   <5ms, 98%+ accuracy                           │  │
│  │   └─────────────────┘                                                  │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│     REDIS       │  │   PROMETHEUS    │  │    GRAFANA      │
│                 │  │                 │  │                 │
│ • Rate limits   │  │ • Metrics       │  │ • Dashboards    │
│ • Cache         │  │ • Alerts        │  │ • Visualization │
│ • AL Queue      │  │ • Histograms    │  │ • Monitoring    │
│ • Sessions      │  │                 │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## MoE (Mixture of Experts) Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    2-STAGE MoE DETECTOR                         │
│                                                                  │
│  Input: "you are worthless garbage"                             │
│                    │                                             │
│                    ▼                                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              STAGE 1: BINARY CLASSIFIER                   │  │
│  │                                                           │  │
│  │  Model: google/muril-base-cased (236M params)            │  │
│  │  Task: Is this toxic or safe?                            │  │
│  │  Output: toxic (0.97 confidence)                         │  │
│  │  Metrics: 95.87% recall, 82.30% F1                       │  │
│  │                                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                    │                                             │
│                    ▼ (if toxic)                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │             STAGE 2: CATEGORY CLASSIFIER                  │  │
│  │                                                           │  │
│  │  Model: google/muril-base-cased (236M params)            │  │
│  │  Task: Which category of toxic content?                  │  │
│  │  Categories:                                              │  │
│  │    • harassment (97% F1)                                  │  │
│  │    • harmful_content (91% F1)                             │  │
│  │    • hate_speech (98% F1)                                 │  │
│  │    • hindi_abuse (99% F1)                                 │  │
│  │    • self_harm (93% F1)                                   │  │
│  │    • sexual (96% F1)                                      │  │
│  │  Output: harassment (0.89 confidence)                    │  │
│  │                                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                    │                                             │
│                    ▼                                             │
│  Final: BLOCK (category=harassment, conf=0.86)                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow
```
Request → Auth → Rate Limit → Validate → Detect → Respond
                                  │
                                  ├── Keywords (sync)
                                  ├── MoE Model (sync)
                                  ├── Claude API (async fallback)
                                  └── PII Regex (sync)
                                  
                                  │
                                  ▼
                            ┌──────────┐
                            │ Response │
                            │          │
                            │ • action │
                            │ • detections │
                            │ • redacted_text │
                            │ • latency_ms │
                            └──────────┘
```

## Feedback & Active Learning
```
┌─────────────────────────────────────────────────────────────────┐
│                    FEEDBACK LOOP                                 │
│                                                                  │
│  User Feedback                                                   │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   /feedback  │ ──▶ │    Redis     │ ──▶ │   Active     │    │
│  │   endpoint   │     │    Queue     │     │   Learner    │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│                                                   │              │
│                                                   ▼              │
│                                            ┌──────────────┐     │
│                                            │   Learned    │     │
│                                            │   Patterns   │     │
│                                            └──────────────┘     │
│                                                   │              │
│                                                   ▼              │
│                                            ┌──────────────┐     │
│                                            │   Retrain    │     │
│                                            │   Pipeline   │     │
│                                            └──────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Deployment Architecture (Future)
```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS CLOUD                                │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    VPC (10.0.0.0/16)                      │  │
│  │                                                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │   ALB       │  │   ECS       │  │ ElastiCache │      │  │
│  │  │ (HTTPS)     │──│  Fargate    │──│   (Redis)   │      │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  │                          │                                │  │
│  │                          ▼                                │  │
│  │                   ┌─────────────┐                        │  │
│  │                   │    S3      │                         │  │
│  │                   │  (Models)  │                         │  │
│  │                   └─────────────┘                        │  │
│  │                                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ CloudWatch  │  │   Cognito   │  │   Secrets   │             │
│  │  (Logs)     │  │   (Auth)    │  │   Manager   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Security Layers
```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY ARCHITECTURE                         │
│                                                                  │
│  Layer 1: Network                                                │
│    • TLS 1.2+ encryption in transit                             │
│    • VPC isolation                                               │
│    • Security groups                                             │
│                                                                  │
│  Layer 2: Authentication                                         │
│    • API key validation                                          │
│    • Tenant isolation                                            │
│    • Key rotation support                                        │
│                                                                  │
│  Layer 3: Authorization                                          │
│    • Tier-based rate limits (free/pro/enterprise)               │
│    • Feature flags per tenant                                    │
│                                                                  │
│  Layer 4: Application                                            │
│    • Input validation                                            │
│    • SQL injection prevention                                    │
│    • Prompt injection detection                                  │
│                                                                  │
│  Layer 5: Data                                                   │
│    • No PII storage by default                                   │
│    • Audit logging                                               │
│    • Data minimization                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
