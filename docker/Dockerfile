# ============================================================================
# TraceBrain - Multi-Stage Dockerfile (Frontend + Backend)
# ============================================================================

# Stage 1: Frontend builder
FROM node:22-alpine AS frontend-builder

WORKDIR /app/web

COPY web/package.json web/package-lock.json ./
RUN npm install

COPY web/ ./
RUN npm run build

# Stage 2: Backend runtime
FROM python:3.11-slim AS backend-runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend source
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY data/ ./data/
COPY scripts/ ./scripts/

# Copy frontend build artifacts into static directory
COPY --from=frontend-builder /app/web/dist /app/src/tracebrain/static

# Install backend package (include local embeddings)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .[embeddings-local]

# Create non-root user
RUN useradd -m -u 1000 tracebrain \
    && mkdir -p /app/logs /app/data \
    && chown -R tracebrain:tracebrain /app

USER tracebrain

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["tracebrain-trace", "start", "--host", "0.0.0.0", "--port", "8000"]
