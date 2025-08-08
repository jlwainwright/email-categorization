# Makefile for Email Categorization System
# Provides convenient commands for Docker operations

.PHONY: help build up down logs test dryrun clean restart

# Default target
help: ## Show this help message
	@echo "Email Categorization System - Docker Commands"
	@echo "============================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development commands
build: ## Build the Docker image
	docker-compose build --no-cache

up: ## Start services in background
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs for all services
	docker-compose logs -f

restart: ## Restart all services
	docker-compose restart

# Testing commands
dryrun: ## Run dry run test (preview mode)
	docker-compose --profile dryrun up email-categorizer-dryrun

test: ## Run one-time categorization test
	docker-compose --profile manual up email-categorizer-manual

# Production commands
prod-up: ## Start production services
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-down: ## Stop production services
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

prod-logs: ## Show production logs
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Monitoring commands
monitoring-up: ## Start with monitoring (Prometheus + Grafana)
	docker-compose --profile monitoring up -d

monitoring-down: ## Stop monitoring services
	docker-compose --profile monitoring down

grafana: ## Open Grafana dashboard
	open http://localhost:3000

# Maintenance commands
clean: ## Clean up containers, networks, and volumes
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

clean-all: ## Clean everything including images
	docker-compose down -v --rmi all
	docker system prune -af

# Configuration commands
config: ## Validate docker-compose configuration
	docker-compose config

config-prod: ## Validate production configuration
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml config

# Debug commands
shell: ## Enter container shell for debugging
	docker-compose exec email-categorizer bash

debug: ## Run container with debugging enabled
	docker-compose run --rm email-categorizer python3 -c "import pdb; pdb.set_trace()"

health: ## Check container health status
	docker-compose ps
	@echo "Container health details:"
	@docker inspect email-categorizer-main --format='Health Status: {{.State.Health.Status}}'

# Development helpers
dev-setup: ## Setup development environment
	cp config.ini.example config.ini
	@echo "Please edit config.ini with your credentials"
	@echo "Then run: make up"

install: ## Install dependencies locally (for development)
	pip install -r requirements.txt

install-local: ## Install dependencies locally with system-managed Python (PEP 668 override)
	pip3 install -r requirements.txt --break-system-packages

check: ## Run a quick compile-time syntax check (no network)
	python3 -m compileall -q .

# Quick actions
quick-start: dev-setup up logs ## Complete setup and start with logs

status: ## Show status of all services
	docker-compose ps
	@echo "\nResource usage:"
	@docker stats --no-stream email-categorizer-main 2>/dev/null || echo "Container not running"

# Data management
backup-logs: ## Backup log files
	mkdir -p backup/$(shell date +%Y%m%d_%H%M%S)
	cp -r logs/ backup/$(shell date +%Y%m%d_%H%M%S)/

backup-config: ## Backup configuration
	mkdir -p backup/config
	cp config.ini backup/config/config_$(shell date +%Y%m%d_%H%M%S).ini