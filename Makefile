.PHONY: help run migrate makemigrations test test-cov lint format typecheck shell celery celery-beat superuser static check build up down logs clean

# ──────────────────────────────────────────────────
# Person Blog — Makefile
# ──────────────────────────────────────────────────

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Development ──────────────────────────────────

run: ## Run Django development server
	python backend/manage.py runserver 0.0.0.0:8000

migrate: ## Apply database migrations
	python backend/manage.py migrate

makemigrations: ## Create new database migrations
	python backend/manage.py makemigrations

shell: ## Open Django shell
	python backend/manage.py shell

superuser: ## Create superuser interactively
	python backend/manage.py createsuperuser

static: ## Collect static files
	python backend/manage.py collectstatic --noinput

check: ## Run Django system checks
	python backend/manage.py check

# ── Testing ──────────────────────────────────────

test: ## Run test suite
	pytest backend/tests/ -v

test-cov: ## Run tests with coverage report
	pytest backend/tests/ --cov --cov-report=html --cov-report=term

# ── Code Quality ─────────────────────────────────

lint: ## Lint code with ruff
	ruff check backend/

format: ## Format code with ruff
	ruff format backend/

typecheck: ## Run mypy type checking
	mypy backend/

# ── Celery ───────────────────────────────────────

celery: ## Start Celery worker
	cd backend && celery -A config worker -l info -E

celery-beat: ## Start Celery beat scheduler
	cd backend && celery -A config beat -l info

# ── Docker ───────────────────────────────────────

build: ## Build Docker images
	docker compose -f docker/docker-compose.yml build

up: ## Start Docker services
	docker compose -f docker/docker-compose.yml up -d

down: ## Stop Docker services
	docker compose -f docker/docker-compose.yml down

logs: ## Tail Docker logs
	docker compose -f docker/docker-compose.yml logs -f

# ── Maintenance ──────────────────────────────────

clean: ## Remove compiled files, caches, and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .mypy_cache .ruff_cache .pytest_cache htmlcov coverage.xml .coverage
