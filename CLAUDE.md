# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Universal Restrictor is a model-agnostic content moderation and PII detection API for LLM safety. It provides a multi-layer detection pipeline with support for English and Indian languages (Hindi/Hinglish), Claude API fallback for edge cases, and active learning feedback loops.

**Python 3.10+ | FastAPI | PyTorch/Transformers | React 19 + TypeScript dashboard**

## Common Commands

### Setup
```bash
make setup          # Full setup: venv + install + .env
make install-dev    # Install with dev deps (pytest, black, ruff, mypy)
```

### Running
```bash
make run            # API server on port 8000 (uses run.sh)
make dev            # Redis + API server
make dev-full       # Redis + Prometheus + Grafana + API
```

### Testing
```bash
make test                          # All tests
pytest tests/ -v                   # All tests directly
pytest tests/test_regex_only.py -v # Quick regex-only tests (no model needed)
pytest tests/test_api.py -v        # API endpoint tests
pytest tests/test_api.py::test_name -v  # Single test
make test-cov                      # Tests with coverage
```

### Code Quality
```bash
make lint           # ruff check + mypy
make format         # black formatting
make check          # lint + test
```
Ruff and Black are configured in `pyproject.toml` with line-length=100, target Python 3.11.

### Dashboard (React)
```bash
cd dashboard && npm install   # Install deps
cd dashboard && npm run dev   # Dev server on port 5173
cd dashboard && npm run build # Production build
```

### Docker
```bash
make up             # Full stack: API + Redis + Prometheus + Grafana
make down           # Stop all services
make docker-build   # Build image only
```

## Architecture

### Detection Pipeline (in order)
The `Restrictor` class in `restrictor/engine.py` orchestrates all detectors in sequence:

1. **Safe phrases check** — skip known-safe content
2. **Keyword patterns** (`restrictor/detectors/toxicity.py`) — regex-based, <1ms, covers Hindi/Hinglish slurs and English threats
3. **MoE Model** (`restrictor/detectors/moe_detector.py`) — 2-stage MuRIL model: Stage 1 binary toxic/safe → Stage 2 category classification (~50ms)
4. **Claude API fallback** (`restrictor/detectors/claude_detector.py`) — for edge cases and low-confidence results (~1-2s)
5. **PII detection** (`restrictor/detectors/pii.py`) — regex for email, phone, Aadhaar, PAN, credit cards, API keys, UPI IDs, etc.

Output: `Decision` with action (ALLOW | ALLOW_WITH_WARNING | REDACT | BLOCK) and list of `Detection` objects.

### Data Models (`restrictor/models.py`)
- `Action` / `Severity` / `Category` enums define the detection taxonomy (26+ categories)
- `Detection` — individual finding with category, severity, confidence, matched_text, position
- `Decision` — aggregate result with action, detections list, request_id, latency
- `PolicyConfig` — per-request configuration for thresholds and toggles

### API Layer (`restrictor/api/`)
- `server.py` — FastAPI app with endpoints: `POST /analyze`, `POST /feedback`, `GET /health`, `GET /metrics`
- Authentication via `X-API-Key` header; keys use `key:tenant:tier` format
- `middleware.py` — Rate limiting (Redis-backed) and Prometheus metrics
- `metrics.py` — Prometheus counters/histograms

### ML Models (`models/`)
- `moe_muril/` — 2-stage MuRIL-based MoE detector (stage1_binary, stage2_category)
- `restrictor-model-final/` — Fallback model
- MoE training done via Colab notebooks in `data/training/`

### Feedback & Active Learning
- `restrictor/feedback/` — Stores user corrections (Redis or file-based)
- `restrictor/training/active_learner.py` — Retrains from feedback

### Infrastructure
- `docker-compose.yml` — API (8000), Redis (6379), Prometheus (9090), Grafana (3001)
- `helm/universal-restrictor/` — Kubernetes Helm chart with HPA, PDB, Ingress
- `grafana/` — Pre-configured dashboards and datasource provisioning

## Key Configuration

- `.env` (from `.env.example`): `API_KEYS`, `ANTHROPIC_API_KEY`, `REDIS_URL`, `RATE_LIMIT`, `CORS_ORIGINS`
- `pyproject.toml`: Ruff rules (E, F, W, I, N selected; E501 and N805 ignored), Black, Pytest config
- Tests in `tests/*` have `E402` (import order) ignored by Ruff
