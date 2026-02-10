.PHONY: help build up down logs test clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d
	@echo "Services starting..."
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/api/docs"
	@echo "Grafana: http://localhost:3001 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"

down: ## Stop all services
	docker-compose down

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs
	docker-compose logs -f backend

test: ## Run tests
	cd backend && pytest tests/ -v

test-cov: ## Run tests with coverage
	cd backend && pytest tests/ -v --cov=app --cov-report=html

clean: ## Clean up containers and volumes
	docker-compose down -v
	rm -rf backend/__pycache__ backend/.pytest_cache
	find . -type d -name "__pycache__" -exec rm -r {} +

restart: down up ## Restart all services

health: ## Check service health
	@echo "Checking backend health..."
	@curl -s http://localhost:8000/api/health | python -m json.tool

shell-backend: ## Shell into backend container
	docker-compose exec backend /bin/bash

shell-db: ## Shell into postgres container
	docker-compose exec postgres psql -U postgres -d ai_support
