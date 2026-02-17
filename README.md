# Universal NLP Restrictor

A production-grade, model-agnostic content moderation and PII detection API with multi-layer detection pipeline.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Tests](https://img.shields.io/badge/tests-22%20passing-brightgreen.svg)

## 🎯 Features

### Detection Pipeline
```
Input Text
    ↓
┌─────────────────────────┐
│ 1. Safe Phrases Check   │ → Skip known safe content
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ 2. Keywords (instant)   │ → 🔑 High-confidence patterns
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ 3. MoE Model (fast)     │ → 🤖 2-Stage MuRIL classifier
│    Stage 1: toxic/safe  │     95.87% recall
│    Stage 2: category    │     96.14% F1
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ 4. Claude API (edge)    │ → 🧠 Complex edge cases
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ 5. PII Detection        │ → 📧 Email, Phone, Aadhaar, etc.
└─────────────────────────┘
```

### Detection Categories
| Category | F1 Score | Detector |
|----------|----------|----------|
| Hindi Abuse | 99% | Keyword + MoE |
| Hate Speech | 98% | MoE |
| Harassment | 97% | MoE |
| Sexual Content | 96% | MoE |
| Self-Harm | 93% | Keyword + MoE |
| Harmful Content | 91% | Keyword + MoE |
| PII (Email, Phone, Aadhaar) | 98%+ | Regex |

### Key Capabilities
- ✅ **Multi-language**: English + Hindi/Hinglish support (MuRIL model)
- ✅ **Model-agnostic**: Works with any LLM (OpenAI, Claude, Gemini, open-source)
- ✅ **Low latency**: <50ms for keyword/MoE, ~1-2s for Claude fallback
- ✅ **Auditable**: Full logging with decision explanations
- ✅ **Feedback loop**: Active learning from corrections

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Redis
- Docker (optional)

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/universal-restrictor.git
cd universal-restrictor

# Setup
make setup
source venv/bin/activate

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start Redis
make redis-up

# Run API
make run
```

### Quick Test
```bash
# Health check
curl http://localhost:8000/health

# Analyze text
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"text": "Hello, how are you?"}'
```

## 📖 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/analyze` | Analyze text for threats/PII |
| POST | `/feedback` | Submit detection feedback |
| GET | `/feedback/stats` | Feedback statistics |
| GET | `/metrics` | Prometheus metrics |

### Analyze Request
```json
{
  "text": "Your text to analyze",
  "policy": {
    "detect_pii": true,
    "detect_toxicity": true,
    "pii_action": "redact",
    "toxicity_action": "block"
  }
}
```

### Analyze Response
```json
{
  "action": "allow|block|redact|warn",
  "detections": [
    {
      "category": "toxic_harassment",
      "severity": "high",
      "confidence": 0.95,
      "detector": "moe_harassment",
      "explanation": "[MOE] MoE detected harassment content"
    }
  ],
  "redacted_text": "...",
  "request_id": "uuid",
  "latency_ms": 45
}
```

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                         API Gateway                          │
│                    (FastAPI + Auth + Rate Limit)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Restrictor Engine                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Keywords │ │   MoE    │ │  Claude  │ │ PII Detector │   │
│  │ Detector │ │ Detector │ │ Detector │ │              │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────────┐
        │  Redis   │   │Prometheus│   │   Grafana    │
        │ (Cache)  │   │(Metrics) │   │ (Dashboard)  │
        └──────────┘   └──────────┘   └──────────────┘
```

### MoE Model Architecture
```
Input Text
    ↓
┌─────────────────────────┐
│   Stage 1: Binary       │  google/muril-base-cased
│   (toxic vs safe)       │  95.87% recall
└─────────────────────────┘
    ↓ (if toxic)
┌─────────────────────────┐
│   Stage 2: Category     │  google/muril-base-cased
│   (6 categories)        │  96.14% F1
└─────────────────────────┘
```

## 🔧 Configuration

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEYS` | API keys (format: `key:tenant:tier`) | Required |
| `ANTHROPIC_API_KEY` | Claude API key for edge cases | Optional |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `PORT` | API port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Policy Configuration
```python
{
    "detect_pii": True,
    "detect_toxicity": True,
    "pii_action": "redact",      # allow, warn, redact, block
    "toxicity_action": "block",   # allow, warn, block
    "pii_types": ["email", "phone", "aadhaar", "pan"],
    "toxicity_threshold": 0.7
}
```

## 📊 Monitoring

### Prometheus Metrics
- `restrictor_requests_total` - Total requests by action
- `restrictor_detections_total` - Detections by category/detector
- `restrictor_request_latency_seconds` - Request latency histogram

### Grafana Dashboard
```bash
make grafana-open
# or visit http://localhost:3001/d/restrictor-main/universal-restrictor
```

## 🧪 Testing
```bash
# Run all tests
make test

# Test detection pipeline
make test-detection

# Quick analyze
make analyze TEXT="your text here"

# Check service status
make status
```

## 🐳 Docker
```bash
# Start all services
make up

# View logs
make logs-docker

# Stop all services
make down
```

## 📁 Project Structure
```
universal-restrictor/
├── restrictor/
│   ├── api/              # FastAPI server
│   ├── detectors/        # Detection modules
│   │   ├── toxicity.py   # Main toxicity detector
│   │   ├── moe_detector.py # MoE model wrapper
│   │   ├── pii.py        # PII detection
│   │   └── claude_detector.py # Claude API fallback
│   ├── training/         # Active learning
│   └── engine.py         # Main orchestration
├── models/
│   └── moe_muril/        # Trained MoE models
│       ├── stage1_binary/
│       └── stage2_category/
├── data/
│   ├── datasets/         # Training data scripts
│   └── training/         # Colab notebooks
├── grafana/              # Dashboard configs
├── tests/
├── docker-compose.yml
├── Makefile
└── README.md
```

## 🔐 Security

- API key authentication
- Rate limiting (Redis-backed)
- Input validation
- Audit logging
- No PII storage by default

## 📈 Performance

| Metric | Value |
|--------|-------|
| Keyword detection | <1ms |
| MoE detection | ~50ms |
| Claude fallback | ~1-2s |
| P95 latency | <100ms |
| Throughput | 1000+ req/s |

## 🛣️ Roadmap

- [x] Multi-layer detection pipeline
- [x] MoE model training (MuRIL)
- [x] Hindi/Hinglish support
- [x] Prometheus + Grafana monitoring
- [x] Active learning feedback loop
- [ ] Stripe billing integration
- [ ] AWS deployment (Terraform)
- [ ] Customer dashboard
- [ ] SDK (Python/JS)

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## React Dashboard

A modern React-based dashboard with full features:

### Features
- 🔐 **Login/Auth** - API key authentication
- 📊 **Dashboard** - Real-time stats, detection rate, feedback overview
- 🔍 **Analyze** - Test content moderation with quick sample buttons
- 📝 **Feedback** - Approve/decline user feedback for training
- 🧠 **Active Learning** - Train model from approved feedback
- 📈 **Metrics** - Live Prometheus metrics visualization
- ⚙️ **Settings** - API key management, rate limits

### Quick Start
```bash
# Install dependencies (first time)
make dashboard-install

# Start dev server
make dashboard

# Open http://localhost:5173
# Login with: sk-dev-1234567890abcdef12345678
```

### Tech Stack
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS v4
- React Router
- React Query
- Lucide Icons
