# syntax=docker/dockerfile:1.7
#
# Hugging Face Space image for agent-generator.
#
# Stage layout:
#   1. spa-build  - node 20 alpine, builds frontend/dist with the `hf`
#                   build channel. Only runs when the SPA source has
#                   actually changed.
#   2. runtime    - python:3.11-slim, installs the slim demo backend and
#                   the published agent-generator generator. Copies the
#                   SPA bundle from stage 1.
#
# The image deliberately ships no shell history, build toolchain, or
# generator source; only the runtime venv, the SPA, and the demo wrapper.

ARG AG_BUILD_CHANNEL=hf
ARG AGENT_GENERATOR_REF=master

# ─── stage 1: SPA bundle ─────────────────────────────────────────────
FROM node:20-alpine AS spa-build

WORKDIR /spa
ENV CI=true \
    npm_config_audit=false \
    npm_config_fund=false

# Install deps first so the layer caches across SPA source edits.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Build the SPA with the `hf` channel. IS_DEMO is true in this bundle.
COPY frontend/ ./
ARG AG_BUILD_CHANNEL
ENV AG_BUILD_CHANNEL=${AG_BUILD_CHANNEL}
RUN npm run build && \
    test -f dist/index.html

# ─── stage 2: runtime ────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    AG_SPACE_PORT=7860

WORKDIR /app

# System deps kept to the minimum needed by cryptography / git+ installs.
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
    && rm -rf /var/lib/apt/lists/*

# Demo backend code (small, hand-written) and shared production
# modules that CI vendors next to space_app/_shared/.
COPY hf/space_app /app/space_app

# Generator + Python runtime deps. The agent-generator wheel exposes
# the same planning_service / build_service used by the production
# CLI and the FastAPI backend.
COPY hf/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt

# SPA bundle from stage 1.
COPY --from=spa-build /spa/dist /app/frontend_dist

# Hugging Face Spaces run as uid 1000 / gid 1000.
RUN groupadd --system --gid 1000 spaceuser && \
    useradd --system --uid 1000 --gid 1000 --create-home spaceuser && \
    chown -R spaceuser:spaceuser /app
USER spaceuser

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; \
        sys.exit(0 if urllib.request.urlopen('http://localhost:7860/health', timeout=3).status == 200 else 1)"

CMD ["python", "-m", "uvicorn", "space_app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "7860", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
