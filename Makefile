POETRY     := poetry
SRC_DIR    := src
REPO_FILE  := $(SRC_DIR)/repository.py
JOB_NAME   := local_ingest_job

DB_CONTAINER  := postgres
DB_USER       := user
DB_PASSWORD   := pwd
DB_NAME       := moovitamix_db
DB_PORT       := 5432
POSTGRES_IMG  := postgres:15

.PHONY: all install serve run-db stop-db ingest ingest-debug ingest-check \
        dagit format unit-test integration-test test coverage clean


# ---------------------
# Project setup
# ---------------------
install:
	@echo "Installing dev environment..."
	@$(POETRY) install --with development

# Run the fastapi server
serve:
	@$(POETRY) run python -m uvicorn main:app --app-dir $(SRC_DIR)/moovitamix_fastapi

# ---------------------
# Local Postgres via Docker
# ---------------------
run-db: stop-db
	@docker run -d \
	  --name $(DB_CONTAINER) \
	  -e POSTGRES_USER=$(DB_USER) \
	  -e POSTGRES_PASSWORD=$(DB_PASSWORD) \
	  -e POSTGRES_DB=$(DB_NAME) \
	  -p $(DB_PORT):$(DB_PORT) \
	  --health-cmd="pg_isready -U $(DB_USER) -d $(DB_NAME)" \
	  --health-interval=5s \
	  --health-retries=10 \
	  $(POSTGRES_IMG)

stop-db:
	-@docker rm -f $(DB_CONTAINER) 2>/dev/null || true

# ---------------------
# Ingestion jobs
# ---------------------
ingest:
	@echo "Running ingestion job…"
	@$(POETRY) run dagster job execute \
	  -f $(REPO_FILE) \
	  -d $(SRC_DIR) \
	  --job $(JOB_NAME)

ingest-debug: # in-process execution for full tracebacks
	@$(POETRY) run dagster job execute \
	  -f $(REPO_FILE) \
	  -d $(SRC_DIR) \
	  --job $(JOB_NAME) \
	  --config src/config/dagster_config.yaml

ingest-check:
	@$(POETRY) run python scripts/check_db.py


# ---------------------
# Dagit UI
# ---------------------
dagit:
	@$(POETRY) run dagster dev -f $(REPO_FILE) -d $(SRC_DIR)

# ---------------------
# Formatting
# ---------------------
format:
	@echo "Formatting..."
	@$(POETRY) run ruff check --select I --fix
	@$(POETRY) run ruff format

# ---------------------
# Testing
# ---------------------
unit-test:
	@echo "Running unit tests."
	@$(POETRY) run pytest tests/unit

integration-test: run-db
	@echo "Waiting for Postgres to be healthy"
	@sleep 5
	@echo "Running integration tests"
	@$(POETRY) run pytest tests/integration
	@$(MAKE) stop-db

test: format unit-test integration-test
	@echo "All tests passed"

coverage: run-db
	@echo "Running tests with coverage report"
	@$(POETRY) run pytest \
	  --cov=src \
	  --cov-config=.coveragerc \
	  --cov-report=term-missing \
	  --cov-report=html:coverage_html \
	  tests
	@echo "Detailed HTML report in ./coverage_html/index.html"
	@$(MAKE) stop-db

# ---------------------
# Cleanup
# ---------------------
clean: stop-db
	@echo "Stopping Postgres container and cleaning up caches, coverage, dagster_home…"
	-@docker rm -f $(DB_CONTAINER) 2>/dev/null || true
	@rm -rf .pytest_cache .cache coverage_html dagster_home
