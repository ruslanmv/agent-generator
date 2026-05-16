# Multi-stage build for the agent-generator backend.
#
# Stage 1 (builder): use uv on python:slim to resolve dependencies into
# a self-contained virtualenv with no build toolchain leaking into the
# final image.
#
# Stage 2 (runtime): copy the venv onto the distroless Python runtime.
# No shell, no apt, ~80 MB final image, runs as the non-root `nonroot`
# user shipped by Distroless.

# ---- builder --------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# Install uv from the official static binary — no network at runtime.
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv

WORKDIR /src

# Resolve dependencies first so they cache across rebuilds.
COPY pyproject.toml ./
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python \
        "fastapi[standard]>=0.115,<0.117" \
        "uvicorn[standard]>=0.32,<0.34" \
        "pydantic>=2.9,<3" \
        "pydantic-settings>=2.6,<3" \
        "sqlalchemy>=2.0,<3" \
        "alembic>=1.13,<2" \
        "aiosqlite>=0.20,<0.21" \
        "asyncpg>=0.30,<0.31" \
        "httpx>=0.27,<0.29" \
        "websockets>=13,<14" \
        "structlog>=24.4,<26" \
        "authlib>=1.3,<2" \
        "pyjwt[crypto]>=2.9,<3" \
        "itsdangerous>=2.2,<3" \
        "argon2-cffi>=23.1,<24" \
        "cryptography>=43,<46"

COPY app ./app
RUN uv pip install --python /opt/venv/bin/python --no-deps .

# ---- runtime --------------------------------------------------------------
FROM gcr.io/distroless/python3-debian12:nonroot AS runtime

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONPATH="/opt/venv/lib/python3.11/site-packages" \
    AG_HOST=0.0.0.0 \
    AG_PORT=8000

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=nonroot:nonroot app ./app

EXPOSE 8000
USER nonroot

# Distroless has no shell, so use the exec-form CMD.
CMD ["/opt/venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
