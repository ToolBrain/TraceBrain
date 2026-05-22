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

# Image profile: full (local embeddings + cloud providers) or slim (cloud-first)
ARG TRACEBRAIN_IMAGE_PROFILE=full

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend source
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Copy frontend build artifacts into static directory
COPY --from=frontend-builder /app/web/dist /app/src/tracebrain/static

# Install backend package and optional dependencies based on selected profile
RUN pip install --no-cache-dir --upgrade pip \
    && if [ "$TRACEBRAIN_IMAGE_PROFILE" = "full" ]; then \
        pip install --no-cache-dir .[embeddings-local,all-llms]; \
    elif [ "$TRACEBRAIN_IMAGE_PROFILE" = "slim" ]; then \
        pip install --no-cache-dir .[all-llms]; \
    else \
        echo "Unsupported TRACEBRAIN_IMAGE_PROFILE: $TRACEBRAIN_IMAGE_PROFILE"; \
        echo "Use TRACEBRAIN_IMAGE_PROFILE=full or TRACEBRAIN_IMAGE_PROFILE=slim"; \
        exit 1; \
    fi

# Create non-root user
RUN useradd -m -u 1000 tracebrain \
    && mkdir -p /app/logs /app/data \
    && chown -R tracebrain:tracebrain /app

USER tracebrain

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["tracebrain", "start", "--host", "0.0.0.0", "--port", "8000"]