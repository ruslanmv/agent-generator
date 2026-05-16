# ────────────────────────────────────────────────────────────────
#  Makefile  –  common tasks for agent-generator
# ────────────────────────────────────────────────────────────────
#
#  Two surfaces live side-by-side in this repo:
#
#    1. The original Python CLI (PyPI: `agent-generator`).
#       Targets:  setup · install · dev-install · lint · format · test
#                 · run · web · dist · docs
#
#    2. The full agent-generator **platform**: FastAPI backend +
#       Vite SPA + Tauri desktop shell + Capacitor mobile shell.
#       Targets:  app-install · app-test · app-start · app-build
#                 and the convenience aliases install-all / test-all
#                 / start / build / stop.
#
#  Both surfaces use the same `python3` toolchain by default.
#  All paths are relative to the repository root.

PYTHON  ?= python3
PIP     ?= $(PYTHON) -m pip
SRC     := src/agent_generator
TESTS   := tests
VENV    := .venv

# Sub-project directories.
BACKEND_DIR  := backend
FRONTEND_DIR := frontend
DESKTOP_DIR  := shells/desktop
MOBILE_DIR   := shells/mobile

# Where the dev servers run.
BACKEND_PORT  ?= 8000
FRONTEND_PORT ?= 5173
LOG_DIR       := .run

# `bash` so the orchestrator targets can use `set -o pipefail` and traps.
SHELL := bash

# ----------------------------------------------------------------
#  Helpers
# ----------------------------------------------------------------
.PHONY: help
help: ## Show this help
	@echo "Common targets:"
	@grep -E '^[a-zA-Z][a-zA-Z0-9_-]+:.*?##' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?##"}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ================================================================
#  CLI surface (original — unchanged behaviour)
# ================================================================

# ----------------------------------------------------------------
#  Environment / setup
# ----------------------------------------------------------------
setup: $(VENV)/bin/activate ## Create virtualenv + install dev deps (CLI)
$(VENV)/bin/activate: pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip wheel
	$(VENV)/bin/pip install -e ".[dev,web,openai]"
	@touch $@

install: ## Editable install of the CLI, then install backend + frontend
	$(PIP) install -e .
	@$(MAKE) --no-print-directory app-install

dev-install: ## Editable install with dev + web + openai extras (CLI)
	$(PIP) install -e ".[dev,web,openai]"

install-extras: ## Install optional extras (web, openai) in editable mode
	$(PIP) install -e ".[web,openai]"

# ----------------------------------------------------------------
#  Code quality
# ----------------------------------------------------------------
lint: ## Ruff + Black --check + isort --check (CLI)
	$(PYTHON) -m ruff check $(SRC) $(TESTS)
	$(PYTHON) -m black --check $(SRC) $(TESTS)
	$(PYTHON) -m isort --check $(SRC) $(TESTS)

format: ## Ruff --fix (incl. unsafe) + Black + isort (CLI)
	$(PYTHON) -m ruff check --fix --unsafe-fixes $(SRC) $(TESTS)
	$(PYTHON) -m black $(SRC) $(TESTS)
	$(PYTHON) -m isort $(SRC) $(TESTS)

type: ## Static type-checking with mypy (CLI)
	$(PYTHON) -m mypy $(SRC)

# ----------------------------------------------------------------
#  Tests
# ----------------------------------------------------------------
test: ## Run CLI tests, then platform (backend + frontend) tests
	pytest -n auto -v
	@$(MAKE) --no-print-directory app-test

# ----------------------------------------------------------------
#  Run / Web (CLI)
# ----------------------------------------------------------------
run: ## CLI prompt — make run PROMPT="..." FRAMEWORK=...  (no args → make start)
	@if [ -z "$(PROMPT)" ] && [ -z "$(FRAMEWORK)" ]; then \
		$(MAKE) --no-print-directory app-start; \
	elif [ -z "$(PROMPT)" ] || [ -z "$(FRAMEWORK)" ]; then \
		echo ""; \
		echo "⚠️  Missing variables"; \
		echo "Usage:"; \
		echo "  make run PROMPT='Your prompt' FRAMEWORK='<framework>'"; \
		echo ""; \
		echo "Or boot the full stack (backend + frontend) with:"; \
		echo "  make start"; \
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
	else \
		$(PYTHON) -m agent_generator.cli "$(PROMPT)" --framework $(FRAMEWORK); \
	fi

web: ## Launch Flask dev server (legacy CLI web UI)
	FLASK_APP=agent_generator.web FLASK_ENV=development flask run

# ----------------------------------------------------------------
#  Documentation
# ----------------------------------------------------------------
docs: ## MkDocs live-reload
	mkdocs serve

docs-build: ## Build static docs into site/
	mkdocs build

docs-deploy: ## Deploy documentation in production
	mkdocs gh-deploy --clean

# ----------------------------------------------------------------
#  Distribution
# ----------------------------------------------------------------
dist: clean-dist ## Build wheel + sdist (CLI)
	$(PYTHON) -m build
	twine check dist/*

clean-dist: ## Remove dist/ & build/ artefacts (CLI)
	rm -rf dist build *.egg-info

# ================================================================
#  Platform surface (FastAPI backend · Vite SPA · Tauri · Capacitor)
# ================================================================

# Convenience aliases — these are what most contributors will type.
install-all: install ## Install CLI + backend + frontend (alias for `install`)

test-all: test ## Run every test suite (alias for `test`)

start: app-start ## Run backend + frontend together (alias for `app-start`)

build: app-build ## Build the production artefacts for this host (alias for `app-build`)

stop: app-stop ## Stop background dev servers started by `make start`

# ----------------------------------------------------------------
#  Install
# ----------------------------------------------------------------
app-install: backend-install frontend-install ## Install backend + frontend deps

backend-install: ## Install the FastAPI backend (editable, with [dev])
	@echo "▸ installing backend (uv preferred, pip fallback)…"
	@cd $(BACKEND_DIR) && ( \
		command -v uv >/dev/null 2>&1 \
			&& uv pip install --system -e ".[dev]" \
			|| $(PIP) install -e ".[dev]" \
	)

frontend-install: ## Install Vite SPA deps
	@echo "▸ installing frontend (npm ci if lockfile present, else npm install)…"
	@cd $(FRONTEND_DIR) && ( \
		[ -f package-lock.json ] && npm ci --no-audit --no-fund \
			|| npm install --no-audit --no-fund \
	)

# ----------------------------------------------------------------
#  Test
# ----------------------------------------------------------------
app-test: backend-test frontend-test ## Run backend + frontend test/build smokes

backend-test: ## pytest + ruff on backend/
	@echo "▸ backend tests"
	@cd $(BACKEND_DIR) && $(PYTHON) -m ruff check app tests || true
	@cd $(BACKEND_DIR) && $(PYTHON) -m pytest --no-cov -q

frontend-test: ## tsc --noEmit + vite build (acts as the SPA's CI gate)
	@echo "▸ frontend type-check + build"
	@cd $(FRONTEND_DIR) && npx tsc --noEmit -p tsconfig.app.json || true
	@cd $(FRONTEND_DIR) && npx vite build

# ----------------------------------------------------------------
#  Run (concurrent backend + frontend)
# ----------------------------------------------------------------
#
#  Boots uvicorn on $(BACKEND_PORT) and `vite` on $(FRONTEND_PORT)
#  in the background. Logs stream to $(LOG_DIR)/{backend,frontend}.log
#  and the PIDs land in $(LOG_DIR)/*.pid so `make stop` can clean up.
#
#  Press Ctrl-C in this shell to stop *and* clean up — the trap takes
#  care of both children even on SIGINT.

app-start: app-stop ## Run backend + frontend at once (Ctrl-C to stop)
	@mkdir -p $(LOG_DIR)
	@echo "▸ backend  → http://localhost:$(BACKEND_PORT)"
	@echo "▸ frontend → http://localhost:$(FRONTEND_PORT)"
	@echo "▸ logs     → $(LOG_DIR)/{backend,frontend}.log  (tail -f to follow)"
	@trap 'echo ""; echo "▸ stopping…"; $(MAKE) --no-print-directory app-stop' INT TERM EXIT; \
	( cd $(BACKEND_DIR) && AG_HOST=0.0.0.0 AG_PORT=$(BACKEND_PORT) \
		$(PYTHON) -m uvicorn app.main:app --reload \
			--host 0.0.0.0 --port $(BACKEND_PORT) \
	) > $(LOG_DIR)/backend.log 2>&1 & \
	echo $$! > $(LOG_DIR)/backend.pid; \
	( cd $(FRONTEND_DIR) && npm run dev -- \
			--host 0.0.0.0 --port $(FRONTEND_PORT) --strictPort \
	) > $(LOG_DIR)/frontend.log 2>&1 & \
	echo $$! > $(LOG_DIR)/frontend.pid; \
	wait

app-stop: ## Stop background dev servers if any are running
	@for f in $(LOG_DIR)/backend.pid $(LOG_DIR)/frontend.pid; do \
		[ -f $$f ] || continue; \
		pid=$$(cat $$f); \
		if [ -n "$$pid" ] && kill -0 $$pid 2>/dev/null; then \
			kill $$pid 2>/dev/null || true; \
		fi; \
		rm -f $$f; \
	done

# ----------------------------------------------------------------
#  Build production artefacts
# ----------------------------------------------------------------
#
#  Builds whatever this host can produce:
#
#    • SPA static bundle           → frontend/dist/
#    • Backend Docker image        → agent-generator-backend:dev
#    • Desktop installer           → shells/desktop/src-tauri/target/
#                                     release/bundle/{dmg,msi,nsis,
#                                     deb,rpm,appimage}/...
#
#  The desktop step picks the right bundle for the host OS:
#    macOS    → .dmg + .app
#    Windows  → .msi + setup .exe
#    Linux    → .deb + .rpm + .AppImage
#
#  The signed / notarised production pipeline lives in
#  .github/workflows/desktop.yml — this target produces the unsigned
#  equivalent for local smoke tests.

UNAME_S := $(shell uname -s 2>/dev/null || echo Unknown)
ifeq ($(UNAME_S),Darwin)
  HOST_BUNDLES ?= app,dmg
else ifeq ($(UNAME_S),Linux)
  HOST_BUNDLES ?= deb,rpm,appimage
else
  # Anything we don't recognise → assume Windows (MINGW, MSYS, CYGWIN).
  HOST_BUNDLES ?= msi,nsis
endif

app-build: build-frontend build-backend-image build-desktop ## Frontend dist + backend image + desktop installer for this host

build-frontend: ## Produce the production SPA bundle in frontend/dist/
	@echo "▸ building frontend (Vite, channel=web)…"
	@cd $(FRONTEND_DIR) && AG_BUILD_CHANNEL=web npm run build

build-backend-image: ## Build the multi-stage backend Docker image
	@command -v docker >/dev/null 2>&1 || { \
		echo "skip: docker not on PATH"; exit 0; }
	@echo "▸ building backend image (agent-generator-backend:dev)…"
	@docker build -t agent-generator-backend:dev $(BACKEND_DIR)

build-desktop: build-frontend ## Build the Tauri installer(s) for the host OS (.dmg / .msi / .AppImage / .deb / .rpm)
	@command -v cargo >/dev/null 2>&1 || { \
		echo "skip: cargo not on PATH (install Rust + the Tauri prerequisites for $(UNAME_S) — see shells/desktop/README.md)"; exit 0; }
	@echo "▸ building desktop bundle(s): $(HOST_BUNDLES)"
	@cd $(DESKTOP_DIR) && ( \
		[ -d node_modules ] || npm install --no-audit --no-fund \
	) && npx tauri build --bundles $(HOST_BUNDLES)
	@echo "▸ artefacts in $(DESKTOP_DIR)/src-tauri/target/release/bundle/"

build-android: build-frontend ## Build the Android debug APK (requires Android SDK + Java 17)
	@command -v java >/dev/null 2>&1 || { \
		echo "skip: java not on PATH (install OpenJDK 17 and the Android SDK)"; exit 0; }
	@echo "▸ building Android debug APK"
	@cd $(MOBILE_DIR) && ( [ -d node_modules ] || npm install --no-audit --no-fund )
	@cd $(MOBILE_DIR) && ( [ -d android ] || npx cap add android )
	@cd $(MOBILE_DIR) && AG_BUILD_CHANNEL=capacitor npx cap sync
	@cd $(MOBILE_DIR)/android && ./gradlew assembleDebug

# ----------------------------------------------------------------
#  Misc
# ----------------------------------------------------------------
clean: clean-dist app-stop ## Remove caches + artefacts + dev-server PIDs
	rm -rf $(VENV) .mypy_cache .pytest_cache .ruff_cache $(LOG_DIR)
	find . -type d -name "__pycache__" -exec rm -rf {} +

.PHONY: help setup install dev-install install-extras lint format type test \
        run web docs docs-build docs-deploy dist clean-dist clean \
        install-all test-all start build stop \
        app-install backend-install frontend-install \
        app-test backend-test frontend-test \
        app-start app-stop \
        app-build build-frontend build-backend-image build-desktop build-android

.DEFAULT_GOAL := help
