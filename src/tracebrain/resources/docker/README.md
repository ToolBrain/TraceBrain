# Docker Configuration for TraceBrain

This directory contains all Docker-related files for running TraceBrain in containers.

## 📁 Files

- **`Dockerfile`** - Production-optimized multi-stage Docker image
- **`docker-compose.yml`** - Orchestrates PostgreSQL + API services
- **`.dockerignore`** - Optimizes build context

## 🚀 Quick Start

### Using CLI (Recommended)

```bash
# From project root
tracebrain up          # Start full image (default)
tracebrain up --slim   # Start slim image (cloud-first)
tracebrain status      # Check status
tracebrain down        # Stop all services
```

### Image Profiles

- **Full (`latest`)**: ~2.8GB, includes local embedding stack (`embeddings-local`), supports `EMBEDDING_PROVIDER=local`.
- **Slim (`slim`)**: ~400-500MB, faster pull/start, intended for cloud embeddings (`EMBEDDING_PROVIDER=openai` or `gemini`).

### Using Docker Compose Directly

```bash
# From project root
# Full image (default)
docker compose -f src/tracebrain/resources/docker/docker-compose.yml up -d --build

# Slim image
TRACEBRAIN_IMAGE=quyk67uet/tracebrain:slim docker compose -f src/tracebrain/resources/docker/docker-compose.yml up -d

# Slim image (PowerShell)
$env:TRACEBRAIN_IMAGE='quyk67uet/tracebrain:slim'; docker compose -f src/tracebrain/resources/docker/docker-compose.yml up -d

# Utility commands
docker compose -f src/tracebrain/resources/docker/docker-compose.yml ps
docker compose -f src/tracebrain/resources/docker/docker-compose.yml logs -f
docker compose -f src/tracebrain/resources/docker/docker-compose.yml down
```

## 🏗️ Architecture

```
┌─────────────────────┐
│   tracebrain-api    │
│   (FastAPI + UI)    │
│   Port: 8000        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   postgres          │
│   (pgvector)        │
│   Port: 5432        │
└─────────────────────┘
```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` at the project root, then customize values as needed:

```env
# Database
DATABASE_URL=postgresql://tracebrain:tracebrain_2026_secure@postgres:5432/tracestore
# POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB are used by the postgres service.
POSTGRES_USER=tracebrain
POSTGRES_PASSWORD=tracebrain_2026_secure
POSTGRES_DB=tracestore

# Server
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info

# LLM API keys (set the providers you plan to use)
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
# ANTHROPIC_API_KEY=your_claude_api_key_here
# HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# Optional provider endpoints/proxies
# OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
# ANTHROPIC_BASE_URL=https://your-anthropic-endpoint
# HUGGINGFACE_BASE_URL=http://localhost:8000

# Bootstrap defaults (used before runtime settings are configured in UI)
DEFAULT_LIBRARIAN_PROVIDER=openai
DEFAULT_LIBRARIAN_MODEL=gpt-4o-mini
DEFAULT_JUDGE_PROVIDER=gemini
DEFAULT_JUDGE_MODEL=gemini-2.5-flash
DEFAULT_CURATOR_PROVIDER=gemini
DEFAULT_CURATOR_MODEL=gemini-2.5-flash

# System
LIBRARIAN_MODE=api
LLM_DEBUG=false

# Optional: choose image profile in Docker mode
# TRACEBRAIN_IMAGE=quyk67uet/tracebrain:latest
# TRACEBRAIN_IMAGE=quyk67uet/tracebrain:slim

# Embedding
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-MiniLM-L6-v2
# EMBEDDING_API_KEY=your_embedding_api_key_here
# EMBEDDING_BASE_URL=https://your-embedding-endpoint/v1
```

Note: `.env.example` and `tracebrain init` are the source of truth for the latest configuration template.

Important:
- You may switch LLM provider/model (Librarian/Judge/Curator) at runtime.
- Keep `EMBEDDING_PROVIDER` + `EMBEDDING_MODEL` stable for one database lifecycle.
- If you change embedding engine, re-embed/migrate existing vectors first; otherwise semantic search may fail due to mixed vector dimensions.

## 📊 Services

### postgres
- **Image**: `ankane/pgvector:v0.5.1`
- **Port**: `5432`
- **Volume**: `tracebrain_postgres_data` (persistent)
- **Health Check**: Automatic readiness probe

Note: The database port is currently exposed for local development. Remove the
`ports` mapping in `docker-compose.yml` for production deployments.

### tracebrain-api
- **Image**: `${TRACEBRAIN_IMAGE:-quyk67uet/tracebrain:latest}`
- **Port**: `8000`
- **Depends on**: postgres (healthy)
- **Health Check**: `/healthz` endpoint
- **Frontend**: Served from the same URL as the API

### tracebrain-seed
- **Purpose**: One-time seed of sample traces
- **Runs**: After `tracebrain-api` is healthy
- **Behavior**: Skips if traces already exist

## ✅ Access URLs

- Frontend UI: http://localhost:8000/
- API Docs: http://localhost:8000/docs
- API Base: http://localhost:8000/api/v1/

## 🔍 Troubleshooting

### Check logs
```bash
docker compose -f src/tracebrain/resources/docker/docker-compose.yml logs tracebrain-api
docker compose -f src/tracebrain/resources/docker/docker-compose.yml logs postgres
```

### Rebuild images
```bash
docker compose -f src/tracebrain/resources/docker/docker-compose.yml up --build
```

### Reset everything (⚠️ deletes data)
```bash
docker compose -f src/tracebrain/resources/docker/docker-compose.yml down -v
```

## 🏭 Production Considerations

1. **Change default passwords** in `docker-compose.yml`
2. **Use secrets** instead of environment variables
3. **Add resource limits** (CPU, memory)
4. **Configure logging driver** (e.g., json-file with rotation)
5. **Use reverse proxy** (nginx, Traefik) for HTTPS
6. **Enable monitoring** (Prometheus, Grafana)
7. **Disable DB port exposure** in production

## 🧪 Building Images (Maintainers)

Build from source with profile ARG:

```bash
# Full image
docker build -f src/tracebrain/resources/docker/Dockerfile \
    --build-arg TRACEBRAIN_IMAGE_PROFILE=full \
    -t quyk67uet/tracebrain:latest .

# Slim image
docker build -f src/tracebrain/resources/docker/Dockerfile \
    --build-arg TRACEBRAIN_IMAGE_PROFILE=slim \
    -t quyk67uet/tracebrain:slim .
```

## 📚 Learn More

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
