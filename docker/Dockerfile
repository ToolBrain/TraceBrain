# ============================================================================
# ToolBrain Tracing - Production Dockerfile
# ============================================================================
# Multi-stage build for optimized image size
# ============================================================================

# Stage 1: Builder
FROM python:3.11-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_PROGRESS_BAR=off \
    PIP_ROOT_USER_ACTION=ignore

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY src/toolbrain_tracing/requirements.txt /build/requirements.txt
COPY pyproject.toml /build/

# Build wheels
RUN pip install --no-cache-dir --upgrade pip --root-user-action=ignore && \
    pip wheel --no-cache-dir -r requirements.txt -w /build/wheels

# Copy application code
COPY src/ /build/src/

# Build application wheel
RUN pip wheel --no-cache-dir . -w /build/wheels

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_PROGRESS_BAR=off \
    PIP_ROOT_USER_ACTION=ignore

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 toolbrain && \
    chown -R toolbrain:toolbrain /app

# Copy wheels from builder and install
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data && \
    chown -R toolbrain:toolbrain /app/logs /app/data

# Switch to non-root user
USER toolbrain

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/toolbrain/.local/bin:$PATH"

# Default command
CMD ["uvicorn", "toolbrain_tracing.main:app", "--host", "0.0.0.0", "--port", "8000"]
