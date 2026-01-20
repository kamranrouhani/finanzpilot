.PHONY: help dev up down logs rebuild test test-backend test-frontend test-e2e lint db-migrate ci-local clean

# Default target
help:
	@echo "FinanzPilot Development Commands"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start all services in dev mode (hot reload)"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make logs         - Follow logs"
	@echo "  make rebuild      - Rebuild and restart containers"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-backend - Run backend tests"
	@echo "  make test-frontend- Run frontend tests"
	@echo "  make test-e2e     - Run E2E tests"
	@echo "  make ci-local     - Run full CI pipeline locally"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         - Run all linters"
	@echo "  make format       - Format all code"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate   - Run database migrations"
	@echo "  make db-reset     - Reset database (WARNING: deletes data)"
	@echo "  make db-backup    - Backup database"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make ollama-pull  - Pull Ollama models"

# ============================================
# Development
# ============================================

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

rebuild:
	docker compose down
	docker compose build --no-cache
	docker compose up -d

# ============================================
# Testing
# ============================================

test: test-backend test-frontend
	@echo "✅ All tests passed"

test-backend:
	@echo "🧪 Running backend tests..."
	docker compose exec backend pytest -v --cov=app --cov-report=term-missing

test-frontend:
	@echo "🧪 Running frontend tests..."
	docker compose exec frontend pnpm test

test-e2e:
	@echo "🧪 Running E2E tests..."
	docker compose exec frontend npx playwright test

test-coverage:
	@echo "📊 Running tests with coverage..."
	docker compose exec backend pytest --cov=app --cov-report=html
	docker compose exec frontend pnpm run test:coverage
	@echo "Coverage reports generated in backend/htmlcov and frontend/coverage"

# ============================================
# Code Quality
# ============================================

lint: lint-backend lint-frontend
	@echo "✅ All linting passed"

lint-backend:
	@echo "🔍 Linting backend..."
	docker compose exec backend black --check .
	docker compose exec backend isort --check-only .
	docker compose exec backend ruff check .

lint-frontend:
	@echo "🔍 Linting frontend..."
	docker compose exec frontend pnpm run lint
	docker compose exec frontend pnpm run type-check

format:
	@echo "🎨 Formatting code..."
	docker compose exec backend black .
	docker compose exec backend isort .
	docker compose exec frontend pnpm run format

# ============================================
# Database
# ============================================

db-migrate:
	@echo "🗃️ Running migrations..."
	docker compose exec backend alembic upgrade head

db-reset:
	@echo "⚠️  Resetting database..."
	docker compose exec backend alembic downgrade base
	docker compose exec backend alembic upgrade head
	@echo "Database reset complete"

db-backup:
	@echo "💾 Backing up database..."
	@mkdir -p backups
	docker compose exec postgres pg_dump -U finanzpilot finanzpilot > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup saved to backups/"

db-shell:
	docker compose exec postgres psql -U finanzpilot finanzpilot

# ============================================
# CI Local
# ============================================

ci-local: lint test
	@echo ""
	@echo "============================================"
	@echo "✅ Local CI passed! Safe to push."
	@echo "============================================"

# ============================================
# Utilities
# ============================================

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf backend/__pycache__
	rm -rf backend/.pytest_cache
	rm -rf backend/htmlcov
	rm -rf frontend/.next
	rm -rf frontend/node_modules/.cache
	rm -rf frontend/coverage
	@echo "Clean complete"

ollama-pull:
	@echo "📥 Pulling Ollama models..."
	docker compose exec ollama ollama pull qwen2.5-vl:7b
	docker compose exec ollama ollama pull qwen2.5:7b
	@echo "Models pulled successfully"

ollama-list:
	docker compose exec ollama ollama list

# ============================================
# Quick shortcuts
# ============================================

b: test-backend
f: test-frontend
t: test
l: lint
