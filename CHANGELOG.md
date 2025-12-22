# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2025-12-22

### Added
- **2-Stage MoE Detector** with MuRIL model (google/muril-base-cased)
  - Stage 1: Binary classifier (toxic/safe) - 95.87% recall
  - Stage 2: Category classifier (6 categories) - 96.14% F1
- **Hindi/Hinglish Support** - Native support for Indian languages
- **Safe Phrase Detection** - Prevents false positives for common greetings
- **English Safe Phrases** - Travel/vacation context detection
- **Grafana Dashboard** - Real-time monitoring with pre-built panels
- **Docker Compose** - Full stack deployment (API + Redis + Prometheus + Grafana)
- **Detection Source Logging** - Debug logs show [KEYWORD], [MOE], [CLAUDE]
- **Test Detection Command** - `make test-detection` for quick pipeline testing

### Changed
- Detection pipeline now: Safe Phrases → Keywords → MoE → Claude → PII
- Improved Makefile with new commands (up, down, status, grafana-open)
- Updated docker-compose.yml with all services

### Fixed
- False positive for "I went back to my country for vacation"
- False positive for "namaste kaise ho"
- MoE model integration with correct Detection model fields

## [0.1.0] - 2025-12-18

### Added
- Initial release
- Keyword-based toxicity detection
- PII detection (email, phone, Aadhaar, PAN)
- Claude API integration for edge cases
- Redis-backed rate limiting
- Prometheus metrics export
- Feedback system with active learning
- Multi-tenant API key authentication
