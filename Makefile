# =============================================================================
# Zenglow — Developer Makefile
# =============================================================================
# Usage:
#   make setup       — first-time setup (copy .env, install deps)
#   make up          — start all Docker services
#   make migrate     — run database migrations
#   make seed        — load seed / demo data
#   make test        — run all tests
#   make lint        — lint all code
#   make build       — production build
#   make down        — stop all services
#   make reset       — full reset (drops DB volumes)
# =============================================================================

.PHONY: help setup up down reset migrate seed logs \
        test test-backend test-frontend \
        lint lint-backend lint-frontend \
        type-check build shell-backend

# ── Colours ───────────────────────────────────────────────────────────────────
CYAN  = \033[0;36m
RESET = \033[0m

help: ## Show this help message
	@echo ""
	@echo "  Zenglow developer commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ── Setup ─────────────────────────────────────────────────────────────────────

setup: ## First-time project setup
	@echo "$(CYAN)Setting up Zenglow...$(RESET)"
	@test -f .env || (cp .env.example .env && echo "  ✓ Created .env from .env.example")
	@which pnpm > /dev/null 2>&1 || npm install -g pnpm@8.15.4
	pnpm install
	@echo "  ✓ Node dependencies installed"
	@echo ""
	@echo "  Next steps:"
	@echo "    make up       — start Docker services"
	@echo "    make migrate  — run DB migrations"
	@echo "    make seed     — load demo data"
	@echo ""

# ── Docker ────────────────────────────────────────────────────────────────────

up: ## Start all services (postgres, redis, backend, celery, frontends)
	docker compose up -d
	@echo "$(CYAN)Services started:$(RESET)"
	@echo "  Customer Web  → http://localhost:3000"
	@echo "  Business Web  → http://localhost:3001"
	@echo "  Admin Web     → http://localhost:3002"
	@echo "  API           → http://localhost:8000"
	@echo "  API Docs      → http://localhost:8000/docs"

up-infra: ## Start only postgres and redis (for local dev without Docker frontends)
	docker compose up -d postgres redis
	@echo "$(CYAN)Infrastructure started (postgres + redis)$(RESET)"

down: ## Stop all services
	docker compose down

reset: ## Stop everything and delete all data volumes (DESTRUCTIVE)
	@echo "$(CYAN)WARNING: This will delete all database data!$(RESET)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
	docker compose down -v
	@echo "  ✓ All volumes deleted"

logs: ## Tail logs for all services
	docker compose logs -f

logs-backend: ## Tail backend logs only
	docker compose logs -f backend

logs-celery: ## Tail Celery worker logs
	docker compose logs -f celery-worker

# ── Database ──────────────────────────────────────────────────────────────────

migrate: ## Run all pending database migrations
	docker compose exec backend alembic upgrade head
	@echo "$(CYAN)✓ Migrations applied$(RESET)"

migrate-local: ## Run migrations against local DB (no Docker)
	cd backend && alembic upgrade head

seed: ## Load development seed data (demo businesses, users, appointments)
	docker compose exec backend python scripts/seed.py
	@echo ""
	@echo "$(CYAN)Demo credentials:$(RESET)"
	@echo "  Platform Admin  admin@zenglow.com    / Admin@1234"
	@echo "  Business Owner  owner@glowstudio.com / Owner@1234"
	@echo "  Staff           staff@glowstudio.com / Staff@1234"
	@echo "  Customer        customer@example.com / Customer@1234"

seed-local: ## Run seed script against local DB (no Docker)
	cd backend && python scripts/seed.py

migration-new: ## Create a new migration (usage: make migration-new MSG="add_xxx_table")
	docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

migration-downgrade: ## Downgrade one migration step
	docker compose exec backend alembic downgrade -1

db-backup: ## Backup the database to ./backups/
	@mkdir -p backups
	docker compose exec -T postgres pg_dump -U zenglow zenglow_db > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(CYAN)✓ Database backed up to ./backups/$(RESET)"

# ── Testing ───────────────────────────────────────────────────────────────────

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend test suite with coverage
	docker compose exec backend pytest tests/ -v --cov=app --cov-report=term-missing

test-backend-local: ## Run backend tests locally (no Docker)
	cd backend && pytest tests/ -v --cov=app --cov-report=term-missing

test-frontend: ## Run all frontend unit tests
	pnpm test

test-customer: ## Run customer-web tests only
	pnpm --filter customer-web test

test-business: ## Run business-web tests only
	pnpm --filter business-web test

test-watch: ## Run frontend tests in watch mode
	pnpm --filter customer-web exec vitest

# ── Linting & Type Checking ───────────────────────────────────────────────────

lint: lint-backend lint-frontend ## Lint all code

lint-backend: ## Lint Python code with ruff
	docker compose exec backend ruff check .
	docker compose exec backend ruff format --check .

lint-backend-local: ## Lint Python locally
	cd backend && ruff check . && ruff format --check .

lint-frontend: ## Lint all Next.js apps
	pnpm lint

type-check: ## TypeScript type-check all apps
	pnpm type-check

format: ## Auto-format all code
	cd backend && ruff format .
	pnpm exec prettier --write "apps/**/*.{ts,tsx}" "packages/**/*.{ts,tsx}"

# ── Build ─────────────────────────────────────────────────────────────────────

build: ## Production build of all frontend apps
	pnpm build

build-docker: ## Build all Docker images
	docker compose build

build-customer: ## Build customer-web Docker image only
	docker build -f infrastructure/docker/Dockerfile.customer-web -t zenglow/customer-web:latest .

build-business: ## Build business-web Docker image only
	docker build -f infrastructure/docker/Dockerfile.business-web -t zenglow/business-web:latest .

build-admin: ## Build admin-web Docker image only
	docker build -f infrastructure/docker/Dockerfile.admin-web -t zenglow/admin-web:latest .

build-backend: ## Build backend Docker image only
	docker build -f infrastructure/docker/Dockerfile.backend -t zenglow/backend:latest .

# ── Dev Utilities ─────────────────────────────────────────────────────────────

shell-backend: ## Open a shell inside the running backend container
	docker compose exec backend bash

shell-db: ## Open psql inside the running postgres container
	docker compose exec postgres psql -U zenglow zenglow_db

health: ## Check health of all running services
	@echo "$(CYAN)Checking service health...$(RESET)"
	@curl -sf http://localhost:8000/health && echo "  ✓ Backend API" || echo "  ✗ Backend API (not running)"
	@curl -sf http://localhost:3000 > /dev/null && echo "  ✓ Customer Web" || echo "  ✗ Customer Web (not running)"
	@curl -sf http://localhost:3001 > /dev/null && echo "  ✓ Business Web" || echo "  ✗ Business Web (not running)"
	@curl -sf http://localhost:3002 > /dev/null && echo "  ✓ Admin Web" || echo "  ✗ Admin Web (not running)"

monitoring: ## Start Celery Flower monitoring (http://localhost:5555)
	docker compose --profile monitoring up -d flower
	@echo "  ✓ Flower → http://localhost:5555"

clean: ## Remove build artifacts, caches
	pnpm clean
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find backend -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find backend -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(CYAN)✓ Cleaned$(RESET)"

install: ## Install all dependencies (pnpm + Python)
	pnpm install
	cd backend && pip install -r requirements-dev.txt
