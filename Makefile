.DEFAULT_GOAL := help
.PHONY: help install up down shell migrate lint format types test-unit test-integration \
        migrations-check security e2e verify ship clean gates

PY      := uv run
MANAGE  := $(PY) python manage.py
DOMAIN  := src/domain src/shared

help: ## Mostrar esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------- entorno ----

install: ## Instalar dependencias y hooks de pre-commit
	uv sync --all-extras
	$(PY) pre-commit install

up: ## Levantar PostgreSQL y Redis
	docker compose up -d
	@echo "Esperando a PostgreSQL..."
	@until docker compose exec -T db pg_isready -q; do sleep 1; done
	@echo "Listo."

down: ## Bajar los servicios
	docker compose down

shell: ## Shell de Django
	$(MANAGE) shell_plus || $(MANAGE) shell

migrate: ## Aplicar migraciones
	$(MANAGE) migrate

# ------------------------------------------------------------- compuertas ----

lint: ## G0 — formato y linting
	$(PY) ruff format --check .
	$(PY) ruff check .

format: ## Aplicar formato (no es compuerta)
	$(PY) ruff format .
	$(PY) ruff check --fix .

types: ## G1 — tipado estatico
	$(PY) mypy src tests

test-unit: ## G2 — tests unitarios + cobertura del dominio
	$(PY) pytest -m "not integration and not e2e" \
		--cov=src/domain --cov=src/shared \
		--cov-report=term-missing --cov-fail-under=85

test-integration: ## G3 — tests de integracion contra PostgreSQL real
	$(PY) pytest -m integration

migrations-check: ## G4 — no faltan migraciones
	$(MANAGE) makemigrations --check --dry-run

security: ## G5 — analisis estatico, dependencias y chequeo de despliegue
	$(PY) bandit -q -r src -c pyproject.toml
	$(PY) pip-audit --strict
	$(MANAGE) check --deploy --fail-level WARNING

e2e: ## G6 — humo del flujo de caja (solo antes de release)
	$(PY) pytest -m e2e

# ------------------------------------------------------------------ meta ----

verify: lint types test-unit test-integration migrations-check security ## G0..G5 — criterio de "tarea hecha"
	@echo ""
	@echo "  VERIFY OK — G0..G5 en verde. La tarea puede cerrarse."

ship: verify e2e ## verify + G6 — criterio de "release"
	@echo ""
	@echo "  SHIP OK — G0..G6 en verde."

gates: ## Estado de cada compuerta por separado, sin cortar al primer fallo
	@for g in lint types test-unit test-integration migrations-check security; do \
		printf "%-20s" "$$g"; \
		if $(MAKE) -s $$g >/dev/null 2>&1; then echo "OK"; else echo "FALLA"; fi; \
	done

clean: ## Limpiar artefactos
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
