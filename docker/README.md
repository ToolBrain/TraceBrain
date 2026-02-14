# Docker Configuration for TraceBrain Tracing

This directory contains all Docker-related files for running TraceBrain Tracing in containers.

## 📁 Files

- **`Dockerfile`** - Production-optimized multi-stage Docker image
- **`docker-compose.yml`** - Orchestrates PostgreSQL + API services
- **`.dockerignore`** - Optimizes build context

## 🚀 Quick Start

### Using CLI (Recommended)

```bash
# From project root
tracebrain-trace up          # Start all services
tracebrain-trace status      # Check status
tracebrain-trace down        # Stop all services
```

### Using Docker Compose Directly

```bash
# From project root
docker compose -f docker/docker-compose.yml up -d --build
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs -f
docker compose -f docker/docker-compose.yml down
```

## 🏗️ Architecture

```
┌─────────────────────┐
│   tracing-api       │
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

Create a `.env` file at the project root (recommended) or edit `docker-compose.yml`:

```env
# Database
POSTGRES_USER=tracebrain
POSTGRES_PASSWORD=tracebrain_2026_secure
POSTGRES_DB=tracestore

# API
DATABASE_URL=postgresql://tracebrain:tracebrain_2026_secure@postgres:5432/tracestore
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info

# Optional: 
LLM_API_KEY=your_key_here
```

## 📊 Services

### postgres
- **Image**: `ankane/pgvector:v0.5.1`
- **Port**: `5432`
- **Volume**: `tracebrain_postgres_data` (persistent)
- **Health Check**: Automatic readiness probe

Note: The database port is not exposed by default in production. Uncomment the
`ports` section in docker-compose.yml for local development only.

### tracing-api
- **Build**: Multi-stage optimized image
- **Port**: `8000`
- **Depends on**: postgres (healthy)
- **Health Check**: `/healthz` endpoint
- **Frontend**: Served from the same URL as the API

### tracebrain-seed
- **Purpose**: One-time seed of sample traces
- **Runs**: After `tracing-api` is healthy
- **Behavior**: Skips if traces already exist

## ✅ Access URLs

- Frontend UI: http://localhost:8000/
- API Docs: http://localhost:8000/docs
- API Base: http://localhost:8000/api/v1/

## 🔍 Troubleshooting

### Check logs
```bash
docker compose -f docker/docker-compose.yml logs tracing-api
docker compose -f docker/docker-compose.yml logs postgres
```

### Rebuild images
```bash
docker compose -f docker/docker-compose.yml up --build
```

### Reset everything (⚠️ deletes data)
```bash
docker compose -f docker/docker-compose.yml down -v
```

## 🏭 Production Considerations

1. **Change default passwords** in `docker-compose.yml`
2. **Use secrets** instead of environment variables
3. **Add resource limits** (CPU, memory)
4. **Configure logging driver** (e.g., json-file with rotation)
5. **Use reverse proxy** (nginx, Traefik) for HTTPS
6. **Enable monitoring** (Prometheus, Grafana)
7. **Disable DB port exposure** in production

## 📚 Learn More

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
