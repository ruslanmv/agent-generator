# ────────────────────────────────────────────────────────────────
#  Makefile  –  common tasks for agent‑generator
# ────────────────────────────────────────────────────────────────

# NOTE:
#   • Use `make <target>` to run a task.
#   • All paths are relative to repository root.
#   • Edit PYTHON ?= python3 if your default is different.

PYTHON  ?= python3
PIP     ?= $(PYTHON) -m pip
SRC     := src/agent_generator
TESTS   := tests
VENV    := .venv

# ----------------------------------------------------------------
#  Helpers
# ----------------------------------------------------------------
.PHONY: help
help:
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?##"}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ----------------------------------------------------------------
#  Environment / setup
# ----------------------------------------------------------------
setup: $(VENV)/bin/activate ## Create virtualenv + install dev deps
$(VENV)/bin/activate: pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip wheel
	$(VENV)/bin/pip install -e ".[dev,web,openai]"
	@touch $@

install: ## Editable install (core only)
	$(PIP) install -e .

dev-install: ## Editable install with dev + web + openai extras
	$(PIP) install -e ".[dev,web,openai]"

install-extras: ## Install optional extras (web, openai) in editable mode
	$(PIP) install -e ".[web,openai]"

# ----------------------------------------------------------------
#  Code quality
# ----------------------------------------------------------------
lint: ## Ruff + Black --check + isort --check
	$(PYTHON) -m ruff check $(SRC) $(TESTS)
	$(PYTHON) -m black --check $(SRC) $(TESTS)
	$(PYTHON) -m isort --check $(SRC) $(TESTS)

format: ## Ruff --fix (incl. unsafe) + Black + isort
	$(PYTHON) -m ruff check --fix --unsafe-fixes $(SRC) $(TESTS)
	$(PYTHON) -m black $(SRC) $(TESTS)
	$(PYTHON) -m isort $(SRC) $(TESTS)

type: ## Static type‑checking with mypy
	$(PYTHON) -m mypy $(SRC)

# ----------------------------------------------------------------
#  Tests
# ----------------------------------------------------------------
test: ## Run pytest in parallel
	pytest -n auto -v

# ----------------------------------------------------------------
#  Run / Web
# ----------------------------------------------------------------
run: ## Quick CLI call – example: make run PROMPT="Build an agent" FRAMEWORK=watsonx_orchestrate
	@if [ -z "$(PROMPT)" ] || [ -z "$(FRAMEWORK)" ]; then \
		echo ""; \
		echo "⚠️  Missing variables"; \
		echo "Usage:"; \
		echo "  make run PROMPT='Your prompt' FRAMEWORK='<framework>'"; \
		echo ""; \
		echo "Supported frameworks:"; \
		echo "  • crewai"; \
		echo "  • crewai_flow"; \
		echo "  • langgraph"; \
		echo "  • react"; \
		echo "  • watsonx_orchestrate"; \
		echo ""; \
		echo "Example:"; \
		echo "  make run PROMPT='Generate a customer service agent for healthcare' FRAMEWORK=watsonx_orchestrate"; \
		exit 1; \
	fi
	$(PYTHON) -m agent_generator.cli "$(PROMPT)" --framework $(FRAMEWORK)

web: ## Launch Flask dev server
	FLASK_APP=agent_generator.web FLASK_ENV=development flask run

# ----------------------------------------------------------------
#  Documentation
# ----------------------------------------------------------------
docs: ## MkDocs live‑reload
	mkdocs serve

docs-build: ## Build static docs into site/
	mkdocs build

docs-deploy: ## Deploy documentation in production 
	mkdocs gh-deploy --clean

# ----------------------------------------------------------------
#  Distribution
# ----------------------------------------------------------------
dist: clean-dist ## Build wheel + sdist
	$(PYTHON) -m build
	twine check dist/*

clean-dist: ## Remove dist/ & build/ artefacts
	rm -rf dist build *.egg-info

# ----------------------------------------------------------------
#  Misc
# ----------------------------------------------------------------
clean: clean-dist ## Remove caches + artefacts
	rm -rf $(VENV) .mypy_cache .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +

.DEFAULT_GOAL := help
