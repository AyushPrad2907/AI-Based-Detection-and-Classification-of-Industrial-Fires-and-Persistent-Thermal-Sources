# =============================================================================
# SIH26162 — Project Task Runner
# =============================================================================
# Usage: make <target>
# =============================================================================

.PHONY: dev-backend dev-frontend test test-backend test-ml lint format \
        docker-up docker-down train ingest clean help

# Default target
help:
	@echo "SIH26162 - Industrial Fire & Thermal AI Detector"
	@echo "================================================"
	@echo "  make dev-backend    Start FastAPI dev server"
	@echo "  make dev-frontend   Start React dev server"
	@echo "  make test           Run all tests"
	@echo "  make test-backend   Run backend tests only"
	@echo "  make test-ml        Run ML tests only"
	@echo "  make lint           Lint Python code with Ruff"
	@echo "  make format         Format Python code with Ruff"
	@echo "  make docker-up      Start all Docker services"
	@echo "  make docker-down    Stop all Docker services"
	@echo "  make train          Train ML model"
	@echo "  make ingest         Ingest FIRMS data to database"
	@echo "  make clean          Remove Python cache files"

# Development servers
dev-backend:
	cd backend && PYTHONPATH=.. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# Testing
test:
	PYTHONPATH=. pytest tests/ -v

test-backend:
	PYTHONPATH=. pytest tests/backend/ -v

test-ml:
	PYTHONPATH=. pytest tests/ml/ -v

# Code quality
lint:
	ruff check backend/ ml/ scripts/ tests/

format:
	ruff format backend/ ml/ scripts/ tests/

# Docker
docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

# ML Pipeline
train:
	PYTHONPATH=. python scripts/train_model.py

ingest:
	PYTHONPATH=. python scripts/ingest_to_db.py

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; true
	find . -type f -name "*.pyc" -delete 2>/dev/null; true
