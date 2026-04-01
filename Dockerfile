# ────────────────────────────────────────────────────────────────
#  Dockerfile  -  production image for agent-generator v1.0.0
# ────────────────────────────────────────────────────────────────
#
#   $ docker build -t agent-generator:latest .
#   $ docker run -e WATSONX_API_KEY=... -p 8000:8000 agent-generator:latest
#
# The container launches a Uvicorn server exposing the FastAPI Web UI
# at http://localhost:8000.  The CLI is also available inside the
# container (`docker run --rm agent-generator agent-generator --help`).
# ------------------------------------------------------------------

FROM python:3.11-alpine AS base

# -------------------------------------------------
# Essential build tools (compile wheels)
# -------------------------------------------------
RUN apk add --no-cache --virtual .build-deps \
      gcc musl-dev libffi-dev openssl-dev

# -------------------------------------------------
# Virtualenv
# -------------------------------------------------
ENV VENV_PATH="/opt/venv"
RUN python -m venv ${VENV_PATH}
ENV PATH="${VENV_PATH}/bin:$PATH"

# -------------------------------------------------
# Copy source and install
# -------------------------------------------------
WORKDIR /app
COPY pyproject.toml README.md LICENSE /app/
COPY src /app/src
RUN pip install --upgrade pip && \
    pip install "."

# -------------------------------------------------
# Clean build deps to slim image
# -------------------------------------------------
RUN apk del .build-deps

# -------------------------------------------------
# Healthcheck
# -------------------------------------------------
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s CMD wget -qO- http://localhost:8000/health || exit 1

# -------------------------------------------------
# Runtime configuration
# -------------------------------------------------
ENV PORT=8000

EXPOSE ${PORT}

CMD ["uvicorn", "agent_generator.wsgi:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
