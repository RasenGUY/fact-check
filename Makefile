# Fact-Check API Makefile
# Commands for development, testing, and operations

SHELL := /bin/bash
ENV_FILE := ./.env
-include $(ENV_FILE)

# Default values
DOCKER_COMPOSE = docker compose
PYTHON = python3

# Default target
.PHONY: help
help:
	@echo "Fact-Check API"
	@echo ""
	@echo "Usage:"
	@echo "  make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  help                Show this help message"
	@echo ""
	@echo "Development:"
	@echo "  setup               Setup complete development environment"
	@echo "  venv                Create Python virtual environment"
	@echo "  env                 Create .env file from template"
	@echo ""
	@echo "Local Development:"
	@echo "  up-api              Setup and start API locally (no Docker)"
	@echo ""
	@echo "Docker:"
	@echo "  build               Build Docker image"
	@echo "  up                  Build and start services in Docker"
	@echo "  down                Stop all services"
	@echo "  down-v              Stop services and remove volumes"
	@echo "  logs                Show logs from all services"
	@echo ""
	@echo "Testing:"
	@echo "  test                Run unit tests"
	@echo "  test-all            Run all tests (unit + integration)"
	@echo "  coverage            Run tests with coverage report"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean               Remove cache and temporary files"
	@echo "  status              Show system status"

# Validation target - checks required environment variables
.PHONY: validate-env
validate-env: env
	@if [ -z "$(OPENROUTER_API_KEY)" ] || [ "$(OPENROUTER_API_KEY)" = "" ]; then \
		echo ""; \
		echo "ERROR: OPENROUTER_API_KEY is not set!"; \
		echo ""; \
		echo "Please add your OpenRouter API key to .env:"; \
		echo "  echo 'OPENROUTER_API_KEY=your-key-here' >> .env"; \
		echo ""; \
		echo "Get your API key at: https://openrouter.ai/keys"; \
		echo ""; \
		exit 1; \
	fi
	@echo "Environment validated: OPENROUTER_API_KEY is set"

# Development setup
.PHONY: setup
setup: env venv
	@echo ""
	@echo "Development environment setup complete!"
	@echo ""
	@if [ -z "$(OPENROUTER_API_KEY)" ] || [ "$(OPENROUTER_API_KEY)" = "" ]; then \
		echo "IMPORTANT: Add your OPENROUTER_API_KEY to .env before running the API"; \
		echo "  echo 'OPENROUTER_API_KEY=your-key-here' >> .env"; \
		echo ""; \
	fi

.PHONY: venv
venv:
	@echo "Creating virtual environment..."
	@if [ ! -d "venv" ]; then \
		$(PYTHON) -m venv venv && \
		source venv/bin/activate && \
		pip install --upgrade pip && \
		pip install -r requirements.txt && \
		echo "Virtual environment created and dependencies installed."; \
	else \
		echo "Virtual environment already exists."; \
	fi

.PHONY: env
env:
	@if [ ! -f .env ]; then \
		echo "Creating .env file from example..."; \
		cp .env.example .env; \
		echo "Created .env file."; \
	else \
		echo ".env file already exists."; \
	fi

# Local development - setup + validate + run
.PHONY: up-api
up-api: setup validate-env
	@echo ""
	@echo "Starting FastAPI development server..."
	@echo "API Documentation: http://localhost:8000/docs"
	@echo "ReDoc: http://localhost:8000/redoc"
	@echo ""
	source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Docker commands - build + validate + run
.PHONY: build
build:
	@echo "Building Docker image..."
	$(DOCKER_COMPOSE) build
	@echo "Build complete"

.PHONY: up
up: env validate-env build
	@echo ""
	@echo "Starting services..."
	$(DOCKER_COMPOSE) up -d
	@echo ""
	@echo "Services started"
	@echo "API Documentation: http://localhost:8000/docs"

.PHONY: down
down:
	@echo "Stopping all services..."
	$(DOCKER_COMPOSE) down
	@echo "All services stopped"

.PHONY: down-v
down-v:
	@echo "Stopping all services and removing volumes..."
	$(DOCKER_COMPOSE) down -v
	@echo "All services stopped and volumes removed"

.PHONY: logs
logs:
	$(DOCKER_COMPOSE) logs -f

# Testing commands
.PHONY: test
test: setup
	@echo "Running unit tests..."
	source venv/bin/activate && $(PYTHON) -m pytest tests/unit/ -v
	@echo "Unit tests completed"

.PHONY: test-all
test-all: setup
	@echo "Running all tests..."
	source venv/bin/activate && $(PYTHON) -m pytest tests/ -v
	@echo "All tests completed"

.PHONY: coverage
coverage: setup
	@echo "Running tests with coverage..."
	source venv/bin/activate && $(PYTHON) -m pytest --cov=app --cov-report=term --cov-report=html tests/
	@echo "Coverage report generated"
	@echo "View HTML report at: htmlcov/index.html"

# Maintenance commands
.PHONY: clean
clean:
	@echo "Cleaning up project..."
	rm -rf htmlcov .coverage .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete"

.PHONY: status
status:
	@echo "System Status:"
	@echo ""
	@echo "=== Environment ==="
	@if [ -f .env ]; then \
		if [ -n "$(OPENROUTER_API_KEY)" ] && [ "$(OPENROUTER_API_KEY)" != "" ]; then \
			echo "OPENROUTER_API_KEY: set"; \
		else \
			echo "OPENROUTER_API_KEY: NOT SET"; \
		fi; \
	else \
		echo ".env file: NOT FOUND"; \
	fi
	@echo ""
	@echo "=== Docker Services ==="
	@$(DOCKER_COMPOSE) ps 2>/dev/null || echo "No Docker services running"
	@echo ""
	@echo "=== FastAPI Process ==="
	@ps aux | grep "uvicorn" | grep -v grep || echo "FastAPI not running locally"
