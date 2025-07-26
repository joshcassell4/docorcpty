# Container Terminal Orchestrator Makefile
SHELL := /bin/bash
.PHONY: help install install-dev test test-unit test-integration test-coverage lint format type-check \
        run run-dev docker-build docker-up docker-down docker-logs clean setup-frontend \
        frontend-install frontend-test frontend-build frontend-dev all-tests pre-commit \
        docker-dev docker-dev-build docker-dev-up docker-dev-down docker-dev-logs docker-dev-shell \
        docker-dev-restart docker-dev-clean

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Project variables
PROJECT_NAME := container-terminal-orchestrator
API_PORT := 8000
FRONTEND_PORT := 3000

help: ## Show this help message
	@echo -e "${BLUE}Container Terminal Orchestrator - Available Commands${NC}"
	@echo -e "${BLUE}=================================================${NC}"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "${GREEN}%-20s${NC} %s\n", $$1, $$2}'

# Dependency Management
install: ## Install production dependencies using uv
	@echo -e "${BLUE}Installing production dependencies...${NC}"
	uv pip install -e .
	@echo -e "${GREEN}Dependencies installed successfully!${NC}"

install-dev: ## Install development dependencies using uv
	@echo -e "${BLUE}Installing development dependencies...${NC}"
	uv pip install -e ".[dev]"
	@echo -e "${GREEN}Development dependencies installed successfully!${NC}"

# Testing Commands
test: ## Run all tests
	@echo -e "${BLUE}Running all tests...${NC}"
	uv run pytest

test-unit: ## Run unit tests only
	@echo -e "${BLUE}Running unit tests...${NC}"
	uv run pytest tests/unit -v

test-integration: ## Run integration tests only
	@echo -e "${BLUE}Running integration tests...${NC}"
	uv run pytest tests/integration -v

test-coverage: ## Run tests with coverage report
	@echo -e "${BLUE}Running tests with coverage...${NC}"
	uv run pytest --cov=orchestrator --cov-report=html --cov-report=term-missing
	@echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"

# Code Quality
lint: ## Run linting checks
	@echo -e "${BLUE}Running linting checks...${NC}"
	uv run ruff check orchestrator tests
	@echo -e "${GREEN}Linting passed!${NC}"

format: ## Format code using black and ruff
	@echo -e "${BLUE}Formatting code...${NC}"
	uv run black orchestrator tests
	uv run ruff check --fix orchestrator tests
	@echo -e "${GREEN}Code formatted successfully!${NC}"

type-check: ## Run type checking with mypy
	@echo -e "${BLUE}Running type checks...${NC}"
	uv run mypy orchestrator
	@echo -e "${GREEN}Type checking passed!${NC}"

pre-commit: ## Run pre-commit checks
	@echo -e "${BLUE}Running pre-commit checks...${NC}"
	uv run pre-commit run --all-files

# Application Commands
run: ## Run the orchestrator in production mode
	@echo -e "${BLUE}Starting Container Terminal Orchestrator...${NC}"
	uv run uvicorn orchestrator.api.app:app --host 0.0.0.0 --port $(API_PORT)

run-dev: ## Run the orchestrator in development mode with hot reload
	@echo -e "${BLUE}Starting Container Terminal Orchestrator (development mode)...${NC}"
	uv run uvicorn orchestrator.api.app:app --host 0.0.0.0 --port $(API_PORT) --reload

# Docker Commands
docker-build: ## Build Docker images
	@echo -e "${BLUE}Building Docker images...${NC}"
	docker-compose build
	@echo -e "${GREEN}Docker images built successfully!${NC}"

docker-up: ## Start Docker containers
	@echo -e "${BLUE}Starting Docker containers...${NC}"
	docker-compose up -d
	@echo -e "${GREEN}Containers started!${NC}"
	@echo -e "${YELLOW}API available at: http://localhost:$(API_PORT)${NC}"
	@echo -e "${YELLOW}Dashboard available at: http://localhost:$(FRONTEND_PORT)${NC}"

docker-down: ## Stop Docker containers
	@echo -e "${BLUE}Stopping Docker containers...${NC}"
	docker-compose down
	@echo -e "${GREEN}Containers stopped!${NC}"

docker-logs: ## View Docker container logs
	docker-compose logs -f

docker-shell: ## Open shell in orchestrator container
	docker-compose exec orchestrator /bin/bash

docker-test: ## Run tests in Docker
	@echo -e "${BLUE}Running tests in Docker...${NC}"
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
	docker-compose -f docker-compose.test.yml down

# Docker Development Commands
docker-dev: ## Start development environment in Docker containers
	@echo -e "${BLUE}Starting containerized development environment...${NC}"
	docker-compose -f docker-compose.dev.yml up --build

docker-dev-build: ## Build development Docker images
	@echo -e "${BLUE}Building development Docker images...${NC}"
	docker-compose -f docker-compose.dev.yml build
	@echo -e "${GREEN}Development images built successfully!${NC}"

docker-dev-up: ## Start development containers in background
	@echo -e "${BLUE}Starting development containers...${NC}"
	docker-compose -f docker-compose.dev.yml up -d
	@echo -e "${GREEN}Development environment is running!${NC}"
	@echo -e "${GREEN}API: http://localhost:$(API_PORT)${NC}"
	@echo -e "${GREEN}Dashboard: http://localhost:$(FRONTEND_PORT)${NC}"

docker-dev-down: ## Stop development containers
	@echo -e "${BLUE}Stopping development containers...${NC}"
	docker-compose -f docker-compose.dev.yml down

docker-dev-logs: ## View development container logs
	docker-compose -f docker-compose.dev.yml logs -f

docker-dev-shell: ## Open shell in development orchestrator container
	docker-compose -f docker-compose.dev.yml exec orchestrator-dev /bin/bash

docker-dev-restart: ## Restart development containers
	@echo -e "${BLUE}Restarting development containers...${NC}"
	docker-compose -f docker-compose.dev.yml restart

docker-dev-clean: ## Remove development containers and volumes
	@echo -e "${YELLOW}WARNING: This will remove all development containers and volumes!${NC}"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose -f docker-compose.dev.yml down -v --remove-orphans; \
		echo -e "${GREEN}Development environment cleaned!${NC}"; \
	fi

# Frontend Commands
frontend-install: ## Install frontend dependencies
	@echo -e "${BLUE}Installing frontend dependencies...${NC}"
	cd dashboard && npm install
	@echo -e "${GREEN}Frontend dependencies installed!${NC}"

frontend-test: ## Run frontend tests
	@echo -e "${BLUE}Running frontend tests...${NC}"
	cd dashboard && npm test

frontend-build: ## Build frontend for production
	@echo -e "${BLUE}Building frontend...${NC}"
	cd dashboard && npm run build
	@echo -e "${GREEN}Frontend built successfully!${NC}"

frontend-dev: ## Run frontend development server
	@echo -e "${BLUE}Starting frontend development server...${NC}"
	cd dashboard && npm start

# Combined Commands
all-tests: test-unit test-integration frontend-test ## Run all tests (backend + frontend)
	@echo -e "${GREEN}All tests completed!${NC}"

check: lint type-check test ## Run all checks (lint, type-check, tests)
	@echo -e "${GREEN}All checks passed!${NC}"

dev: ## Start both backend and frontend in development mode
	@echo -e "${BLUE}Starting development environment...${NC}"
	@make -j 2 run-dev frontend-dev

# Setup Commands
setup: install-dev frontend-install ## Complete development environment setup
	@echo -e "${BLUE}Setting up pre-commit hooks...${NC}"
	uv run pre-commit install
	@echo -e "${GREEN}Development environment setup complete!${NC}"

init-config: ## Initialize configuration files from examples
	@echo -e "${BLUE}Initializing configuration files...${NC}"
	@test -f .env || (cp .env.sample .env && echo -e "${GREEN}Created .env file${NC}")
	@test -d configs || mkdir -p configs
	@test -f configs/orchestrator.json || (echo {} > configs/orchestrator.json && echo -e "${GREEN}Created orchestrator.json${NC}")

# Cleanup Commands
clean: ## Clean build artifacts and cache
	@echo -e "${BLUE}Cleaning build artifacts...${NC}"
	@python -c "import shutil, os; [shutil.rmtree(os.path.join(r, d)) for r, dirs, _ in os.walk('.') for d in dirs if d in ['__pycache__', '.pytest_cache', '.mypy_cache', 'htmlcov', '.coverage']]" 2>/dev/null || true
	@python -c "import os; [os.remove(os.path.join(r, f)) for r, _, files in os.walk('.') for f in files if f.endswith('.pyc')]" 2>/dev/null || true
	@python -c "import shutil, os; [shutil.rmtree(p) if os.path.exists(p) else None for p in ['dashboard/build', 'dashboard/node_modules/.cache']]" 2>/dev/null || true
	@echo -e "${GREEN}Cleanup complete!${NC}"

clean-docker: ## Remove Docker containers and images
	@echo -e "${BLUE}Cleaning Docker resources...${NC}"
	docker-compose down -v --rmi local
	@echo -e "${GREEN}Docker cleanup complete!${NC}"

# Documentation
docs: ## Generate API documentation
	@echo -e "${BLUE}Generating API documentation...${NC}"
	uv run python -m orchestrator.api.app --generate-openapi > docs/openapi.json
	@echo -e "${GREEN}API documentation generated!${NC}"

# Git Repository Setup
git-init: ## Initialize git repository and make initial commit
	@echo -e "${BLUE}Initializing git repository...${NC}"
	git init
	git add -A
	git commit -m "Initial commit: Container Terminal Orchestrator"
	@echo -e "${GREEN}Git repository initialized!${NC}"

github-create: ## Create GitHub repository and push
	@echo -e "${BLUE}Creating GitHub repository...${NC}"
	gh repo create docorcpty --public --description "Container Terminal Orchestrator - Python-based container orchestration platform"
	git remote add origin https://github.com/$$(gh api user --jq .login)/docorcpty.git
	git push -u origin main
	@echo -e "${GREEN}GitHub repository created and code pushed!${NC}"

# Quick Start
quickstart: setup init-config docker-build ## Quick start for new developers
	@echo -e "${GREEN}========================================${NC}"
	@echo -e "${GREEN}Container Terminal Orchestrator is ready!${NC}"
	@echo -e "${GREEN}========================================${NC}"
	@echo -e ""
	@echo -e "To start the application:"
	@echo -e "  ${YELLOW}make dev${NC}           - Start in development mode"
	@echo -e "  ${YELLOW}make docker-up${NC}     - Start with Docker"
	@echo -e ""
	@echo -e "To run tests:"
	@echo -e "  ${YELLOW}make test${NC}          - Run all tests"
	@echo -e "  ${YELLOW}make test-coverage${NC} - Run tests with coverage"
	@echo -e ""
	@echo -e "For more commands: ${YELLOW}make help${NC}"