# =============================================================================
# Universal Restrictor - Makefile
# =============================================================================
# Usage: make <target>
# Run `make help` to see all available targets
# =============================================================================

.PHONY: help install dev setup run test lint clean docker helm dashboard monitoring train all

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip
VENV := venv
PORT := 8000
DOCKER_IMAGE := universal-restrictor
HELM_RELEASE := restrictor

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# =============================================================================
# HELP
# =============================================================================

help: ## Show this help message
	@echo ""
	@echo "$(BLUE)Universal Restrictor - Available Commands$(NC)"
	@echo "==========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# SETUP & INSTALLATION
# =============================================================================

venv: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)Virtual environment created. Run 'source venv/bin/activate'$(NC)"

install: ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Dependencies installed.$(NC)"

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing dev dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-cov black ruff mypy
	@echo "$(GREEN)Dev dependencies installed.$(NC)"

setup: venv ## Full setup (venv + install + env file)
	@echo "$(BLUE)Setting up project...$(NC)"
	. $(VENV)/bin/activate && $(PIP) install -r requirements.txt
	@if [ ! -f .env ]; then cp .env.example .env; echo "$(YELLOW)Created .env from .env.example - please edit with your keys$(NC)"; fi
	@mkdir -p data/prometheus data/grafana grafana/dashboards grafana/provisioning/datasources grafana/provisioning/dashboards
	@echo "$(GREEN)Setup complete!$(NC)"

env: ## Create .env file from example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)Created .env file. Please edit with your API keys.$(NC)"; \
	else \
		echo "$(YELLOW).env already exists. Skipping.$(NC)"; \
	fi

# =============================================================================
# RUNNING
# =============================================================================

run: ## Run the API server
	@echo "$(BLUE)Starting API server on port $(PORT)...$(NC)"
	./run.sh

run-prod: ## Run in production mode (no reload)
	@echo "$(BLUE)Starting API server in production mode...$(NC)"
	uvicorn restrictor.api.server:app --host 0.0.0.0 --port $(PORT) --workers 4

run-script: ## Run using run.sh script
	./run.sh

dashboard: ## Open admin dashboard in browser
	@echo "$(BLUE)Opening dashboard...$(NC)"
	@open http://localhost:$(PORT)/docs || xdg-open http://localhost:$(PORT)/docs

# =============================================================================
# TESTING
# =============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest tests/ -v --cov=restrictor --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)Coverage report: htmlcov/index.html$(NC)"

test-quick: ## Run quick regex-only tests
	@echo "$(BLUE)Running quick tests...$(NC)"
	pytest tests/test_regex_only.py -v

test-detection: ## Test detection pipeline
	@echo "$(BLUE)Testing detection pipeline...$(NC)"
	@echo "1. Keyword (bhenchod):"
	@curl -s -X POST http://localhost:$(PORT)/analyze -H "Content-Type: application/json" -H "X-API-Key: sk-dev-1234567890abcdef12345678" -d '{"text": "bhenchod"}' | python -c "import sys,json; r=json.load(sys.stdin); print(f'   {r[\"action\"]} | {r[\"detections\"][0][\"detector\"] if r[\"detections\"] else \"none\"}')"
	@echo "2. MoE (harassment):"
	@curl -s -X POST http://localhost:$(PORT)/analyze -H "Content-Type: application/json" -H "X-API-Key: sk-dev-1234567890abcdef12345678" -d '{"text": "you are worthless garbage"}' | python -c "import sys,json; r=json.load(sys.stdin); print(f'   {r[\"action\"]} | {r[\"detections\"][0][\"detector\"] if r[\"detections\"] else \"none\"}')"
	@echo "3. Safe (hello):"
	@curl -s -X POST http://localhost:$(PORT)/analyze -H "Content-Type: application/json" -H "X-API-Key: sk-dev-1234567890abcdef12345678" -d '{"text": "Hello, how are you?"}' | python -c "import sys,json; r=json.load(sys.stdin); print(f'   {r[\"action\"]}')"
	@echo "4. PII (email):"
	@curl -s -X POST http://localhost:$(PORT)/analyze -H "Content-Type: application/json" -H "X-API-Key: sk-dev-1234567890abcdef12345678" -d '{"text": "My email is test@example.com"}' | python -c "import sys,json; r=json.load(sys.stdin); print(f'   {r[\"action\"]} | {r[\"detections\"][0][\"detector\"] if r[\"detections\"] else \"none\"}')"

# =============================================================================
# CODE QUALITY
# =============================================================================

lint: ## Run linters (ruff + mypy)
	@echo "$(BLUE)Running linters...$(NC)"
	ruff check restrictor/
	mypy restrictor/ --ignore-missing-imports

format: ## Format code with black
	@echo "$(BLUE)Formatting code...$(NC)"
	black restrictor/ tests/
	@echo "$(GREEN)Code formatted.$(NC)"

check: lint test ## Run linters and tests

# =============================================================================
# DOCKER
# =============================================================================

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t $(DOCKER_IMAGE) .
	@echo "$(GREEN)Docker image built: $(DOCKER_IMAGE)$(NC)"

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	docker run -p $(PORT):8000 \
		-e API_KEYS="$${API_KEYS:-test-key:test:free}" \
		-e ANTHROPIC_API_KEY="$${ANTHROPIC_API_KEY:-}" \
		-e REDIS_URL="$${REDIS_URL:-}" \
		$(DOCKER_IMAGE)

docker-push: ## Push to Docker registry (set DOCKER_REGISTRY env var)
	@echo "$(BLUE)Pushing Docker image...$(NC)"
	docker tag $(DOCKER_IMAGE) $${DOCKER_REGISTRY}/$(DOCKER_IMAGE):latest
	docker push $${DOCKER_REGISTRY}/$(DOCKER_IMAGE):latest

docker-clean: ## Remove Docker image
	@echo "$(BLUE)Removing Docker image...$(NC)"
	docker rmi $(DOCKER_IMAGE) || true

# =============================================================================
# DOCKER COMPOSE
# =============================================================================

up: ## Start all services (API + Redis + Prometheus + Grafana)
	@echo "$(BLUE)Starting all services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)All services started!$(NC)"
	@make urls

down: ## Stop all services
	@echo "$(BLUE)Stopping all services...$(NC)"
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs-docker: ## View Docker logs
	docker-compose logs -f

# =============================================================================
# KUBERNETES / HELM
# =============================================================================

helm-install: ## Install Helm chart
	@echo "$(BLUE)Installing Helm chart...$(NC)"
	helm install $(HELM_RELEASE) ./helm/universal-restrictor \
		--set secrets.apiKeys="$${API_KEYS:-test-key:test:free}" \
		--set secrets.anthropicApiKey="$${ANTHROPIC_API_KEY:-}"

helm-upgrade: ## Upgrade Helm release
	@echo "$(BLUE)Upgrading Helm release...$(NC)"
	helm upgrade $(HELM_RELEASE) ./helm/universal-restrictor --reuse-values

helm-uninstall: ## Uninstall Helm release
	@echo "$(BLUE)Uninstalling Helm release...$(NC)"
	helm uninstall $(HELM_RELEASE)

helm-template: ## Render Helm templates (dry-run)
	@echo "$(BLUE)Rendering Helm templates...$(NC)"
	helm template $(HELM_RELEASE) ./helm/universal-restrictor

helm-lint: ## Lint Helm chart
	@echo "$(BLUE)Linting Helm chart...$(NC)"
	helm lint ./helm/universal-restrictor

k8s-port-forward: ## Port forward to Kubernetes service
	kubectl port-forward svc/$(HELM_RELEASE)-universal-restrictor $(PORT):8000

# =============================================================================
# MONITORING (Prometheus + Grafana)
# =============================================================================

monitoring-up: ## Start Prometheus and Grafana
	@echo "$(BLUE)Starting monitoring stack...$(NC)"
	docker-compose up -d prometheus grafana
	@echo "$(GREEN)Prometheus: http://localhost:9090$(NC)"
	@echo "$(GREEN)Grafana: http://localhost:3001 (admin/admin)$(NC)"

monitoring-down: ## Stop Prometheus and Grafana
	@echo "$(BLUE)Stopping monitoring stack...$(NC)"
	docker-compose stop prometheus grafana

monitoring-logs: ## View monitoring logs
	docker-compose logs -f prometheus grafana

grafana-open: ## Open Grafana dashboard in browser
	@open http://localhost:3001/d/restrictor-main/universal-restrictor || xdg-open http://localhost:3001/d/restrictor-main/universal-restrictor

# =============================================================================
# REDIS
# =============================================================================

redis-up: ## Start Redis container
	@echo "$(BLUE)Starting Redis...$(NC)"
	docker run -d --name redis -p 6379:6379 redis:alpine 2>/dev/null || echo "$(YELLOW)Redis already running$(NC)"
	@echo "$(GREEN)Redis running on localhost:6379$(NC)"

redis-down: ## Stop Redis container
	@echo "$(BLUE)Stopping Redis...$(NC)"
	docker stop redis 2>/dev/null || true
	docker rm redis 2>/dev/null || true

redis-cli: ## Open Redis CLI
	docker exec -it redis redis-cli

redis-flush: ## Flush Redis data
	@echo "$(BLUE)Flushing Redis...$(NC)"
	redis-cli FLUSHALL
	@echo "$(GREEN)Redis flushed.$(NC)"

# =============================================================================
# TRAINING & MODELS
# =============================================================================

train: ## Run active learning training job
	@echo "$(BLUE)Running training job...$(NC)"
	$(PYTHON) -m restrictor.training.active_learner

train-moe: ## Instructions to train MoE model
	@echo "$(BLUE)MoE Training Instructions$(NC)"
	@echo "========================="
	@echo "1. Open Google Colab with GPU (T4 or better)"
	@echo "2. Upload: data/training/train_moe_2stage_muril.ipynb"
	@echo "3. Upload: data/datasets/moe/router_train_v2.jsonl"
	@echo "4. Run all cells (~1.5 hours)"
	@echo "5. Download moe_muril.zip"
	@echo "6. Extract to models/moe_muril/"

patterns: ## Show learned patterns
	@echo "$(BLUE)Learned patterns:$(NC)"
	@cat restrictor/detectors/learned_patterns.json 2>/dev/null || echo "No learned patterns yet"

model-check: ## Check if MoE models are loaded
	@echo "$(BLUE)Checking models...$(NC)"
	@ls -lh models/moe_muril/stage1_binary/ 2>/dev/null || echo "$(RED)Stage 1 model not found$(NC)"
	@ls -lh models/moe_muril/stage2_category/ 2>/dev/null || echo "$(RED)Stage 2 model not found$(NC)"
	@echo "$(GREEN)Model check complete.$(NC)"

# =============================================================================
# UTILITIES
# =============================================================================

clean: ## Clean up build artifacts
	@echo "$(BLUE)Cleaning up...$(NC)"
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache htmlcov .coverage
	rm -rf *.egg-info dist build
	rm -rf .mypy_cache .ruff_cache
	@echo "$(GREEN)Cleaned.$(NC)"

clean-all: clean docker-clean ## Clean everything including Docker
	rm -rf $(VENV)
	rm -rf data/prometheus data/grafana
	@echo "$(GREEN)All cleaned.$(NC)"

logs: ## Tail API logs
	tail -f data/audit.log 2>/dev/null || echo "No audit log found. Set AUDIT_LOG_FILE in .env"

health: ## Check API health
	@curl -s http://localhost:$(PORT)/health | python -m json.tool || echo "$(RED)API not running$(NC)"

analyze: ## Quick analyze test (usage: make analyze TEXT="your text")
	@curl -s -X POST http://localhost:$(PORT)/analyze \
		-H "Content-Type: application/json" \
		-H "X-API-Key: sk-dev-1234567890abcdef12345678" \
		-d '{"text": "$(TEXT)"}' | python -m json.tool

status: ## Check status of all services
	@echo "$(BLUE)Service Status$(NC)"
	@echo "==============="
	@echo -n "API:        " && curl -s http://localhost:$(PORT)/health | python -c "import sys,json; print(json.load(sys.stdin).get('status','down'))" 2>/dev/null || echo "$(RED)down$(NC)"
	@echo -n "Redis:      " && redis-cli ping 2>/dev/null || echo "$(RED)down$(NC)"
	@echo -n "Prometheus: " && curl -s http://localhost:9090/-/healthy >/dev/null && echo "$(GREEN)healthy$(NC)" || echo "$(RED)down$(NC)"
	@echo -n "Grafana:    " && curl -s http://localhost:3001/api/health >/dev/null && echo "$(GREEN)healthy$(NC)" || echo "$(RED)down$(NC)"

# =============================================================================
# DEVELOPMENT WORKFLOW
# =============================================================================

dev: redis-up run ## Start Redis + API server for development

dev-full: redis-up monitoring-up run ## Start full dev stack (Redis + Monitoring + API)

all: setup test docker-build ## Full build: setup, test, docker build

# =============================================================================
# QUICK REFERENCE
# =============================================================================

urls: ## Show all service URLs
	@echo ""
	@echo "$(BLUE)Service URLs$(NC)"
	@echo "============"
	@echo "API:        http://localhost:$(PORT)"
	@echo "Swagger:    http://localhost:$(PORT)/docs"
	@echo "Metrics:    http://localhost:$(PORT)/metrics"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana:    http://localhost:3001 (admin/admin)"
	@echo "Dashboard:  http://localhost:3001/d/restrictor-main/universal-restrictor"
	@echo "Redis:      localhost:6379"
	@echo ""
