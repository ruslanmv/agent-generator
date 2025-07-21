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
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?##"}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

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

dev-install: ## Editable install with dev + web extras
	$(PIP) install -e ".[dev,web]"

# ----------------------------------------------------------------
#  Code quality
# ----------------------------------------------------------------
lint: ## Ruff + Black --check + isort --check
	ruff check $(SRC) $(TESTS)
	black --check $(SRC) $(TESTS)
	isort --check $(SRC) $(TESTS)

format: ## Ruff --fix + Black + isort
	ruff check --fix $(SRC) $(TESTS)
	black $(SRC) $(TESTS)
	isort $(SRC) $(TESTS)

type: ## Static type‑checking with mypy
	mypy $(SRC)

# ----------------------------------------------------------------
#  Tests
# ----------------------------------------------------------------
test: ## Run pytest in parallel
	pytest -n auto -v

# ----------------------------------------------------------------
#  Run / Web
# ----------------------------------------------------------------
run: ## Quick CLI call: make run PROMPT="Your prompt" FRAMEWORK=react
	@if [ -z "$(PROMPT)" ]; then \
		echo "Usage: make run PROMPT='...' FRAMEWORK=<fw>"; exit 1; \
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
