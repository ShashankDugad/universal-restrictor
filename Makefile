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
	@mkdir -p data/prometheus data/grafana
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
	uvicorn restrictor.api.server:app --host 0.0.0.0 --port $(PORT) --reload

run-prod: ## Run in production mode (no reload)
	@echo "$(BLUE)Starting API server in production mode...$(NC)"
	uvicorn restrictor.api.server:app --host 0.0.0.0 --port $(PORT) --workers 4

run-script: ## Run using run.sh script
	./run.sh

dashboard: ## Start the admin dashboard
	@echo "$(BLUE)Starting dashboard on http://localhost:3000/standalone.html$(NC)"
	cd dashboard && $(PYTHON) -m http.server 3000

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

test-sentences: ## Run sentence accuracy tests
	@echo "$(BLUE)Running sentence tests...$(NC)"
	pytest tests/test_sentences.py -v

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
	@mkdir -p data/prometheus data/grafana
	docker run -d --name prometheus -p 9090:9090 \
		-v $(PWD)/prometheus.yml:/etc/prometheus/prometheus.yml \
		-v $(PWD)/data/prometheus:/prometheus \
		--add-host=host.docker.internal:host-gateway \
		prom/prometheus || echo "$(YELLOW)Prometheus already running$(NC)"
	docker run -d --name grafana -p 3001:3000 \
		-v $(PWD)/data/grafana:/var/lib/grafana \
		grafana/grafana || echo "$(YELLOW)Grafana already running$(NC)"
	@echo "$(GREEN)Prometheus: http://localhost:9090$(NC)"
	@echo "$(GREEN)Grafana: http://localhost:3001 (admin/admin)$(NC)"

monitoring-down: ## Stop Prometheus and Grafana
	@echo "$(BLUE)Stopping monitoring stack...$(NC)"
	docker stop prometheus grafana || true
	docker rm prometheus grafana || true

monitoring-logs: ## View monitoring logs
	docker logs -f prometheus & docker logs -f grafana

# =============================================================================
# REDIS
# =============================================================================

redis-up: ## Start Redis container
	@echo "$(BLUE)Starting Redis...$(NC)"
	docker run -d --name redis -p 6379:6379 redis:alpine || echo "$(YELLOW)Redis already running$(NC)"
	@echo "$(GREEN)Redis running on localhost:6379$(NC)"

redis-down: ## Stop Redis container
	@echo "$(BLUE)Stopping Redis...$(NC)"
	docker stop redis || true
	docker rm redis || true

redis-cli: ## Open Redis CLI
	docker exec -it redis redis-cli

# =============================================================================
# TRAINING & FEEDBACK
# =============================================================================

train: ## Run active learning training job
	@echo "$(BLUE)Running training job...$(NC)"
	$(PYTHON) -m restrictor.training.active_learner

patterns: ## Show learned patterns
	@echo "$(BLUE)Learned patterns:$(NC)"
	@cat restrictor/detectors/learned_patterns.json 2>/dev/null || echo "No learned patterns yet"

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
		-H "X-API-Key: $${API_KEY:-test-key}" \
		-d '{"text": "$(TEXT)"}' | python -m json.tool

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
	@echo "Dashboard:  http://localhost:3000/standalone.html"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana:    http://localhost:3001"
	@echo "Redis:      localhost:6379"
	@echo ""
