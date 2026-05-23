# syntax=docker/dockerfile:1.7
# DAMAY api — multi-stage Python 3.12 with uv.
# Target final image: sub-300MB.

# ---------- Stage 1: builder ----------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv (pinned).
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /usr/local/bin/

WORKDIR /build

# Install deps first for cache reuse.
COPY apps/api/pyproject.toml apps/api/uv.lock* ./
RUN --mount=type=cache,id=uv,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev || uv sync --no-install-project --no-dev

# Now copy source + sync the project itself.
COPY apps/api/ ./
RUN --mount=type=cache,id=uv,target=/root/.cache/uv \
    uv sync --frozen --no-dev || uv sync --no-dev

# ---------- Stage 2: runtime ----------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    VIRTUAL_ENV=/opt/venv \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl tini ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system --gid 1001 apiuser \
    && adduser --system --uid 1001 --ingroup apiuser apiuser

WORKDIR /app

COPY --from=builder --chown=apiuser:apiuser /opt/venv /opt/venv
COPY --from=builder --chown=apiuser:apiuser /build /app

USER apiuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
