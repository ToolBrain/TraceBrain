"""
TraceBrain Tracing - Main Application Entry Point

This module initializes the FastAPI application and configures all middleware,
routers, and static file serving. It implements the "pip install and run"
philosophy by serving both the API and the React frontend from a single process.

Usage:
    from tracebrain.main import app
    
    # Run with uvicorn
    uvicorn tracebrain.main:app --host 0.0.0.0 --port 8000
    
    # Or use the CLI
    tracebrain-trace start
"""

from pathlib import Path
import logging
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse

from .config import settings
from .api.v1.endpoints import router as api_v1_router

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global state for application resources
app_state = {
    "db_engine": None,
}

def _redact_db_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.username or parsed.password:
        netloc = parsed.hostname or ""
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        return parsed._replace(netloc=netloc).geturl()
    return url

# ============================================================================
# Application Lifespan Events
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for application startup and shutdown.
    
    This replaces the deprecated @app.on_event decorators.
    Handles initialization and cleanup of resources like database connections.
    """
    # ========================================================================
    # STARTUP LOGIC
    # ========================================================================
    logger.info("=" * 70)
    logger.info("TraceBrain Tracing API - Starting Up")
    logger.info("=" * 70)
    logger.info(f"Database: {_redact_db_url(settings.DATABASE_URL)}")
    logger.info(f"Backend Type: {settings.get_backend_type()}")
    logger.info(f"Host: {settings.HOST}:{settings.PORT}")
    logger.info(f"Log Level: {settings.LOG_LEVEL}")
    logger.info(f"API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    
    # Initialize database engine and create tables
    try:
        from .db.session import get_engine, create_tables
        logger.info("Initializing database engine...")
        app_state["db_engine"] = get_engine()
        
        logger.info("Creating database tables if not exist...")
        create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    # Check static directory
    package_dir = Path(__file__).parent
    static_dir = package_dir / settings.STATIC_DIR
    
    if static_dir.exists():
        logger.info(f"Frontend: http://{settings.HOST}:{settings.PORT}/")
    else:
        logger.info("Frontend: Not available (static files not found)")
    
    logger.info("=" * 70)
    logger.info("Application startup complete")
    logger.info("=" * 70)
    
    # Yield control to the application
    yield
    
    # ========================================================================
    # SHUTDOWN LOGIC
    # ========================================================================
    logger.info("=" * 70)
    logger.info("TraceBrain Tracing API - Shutting Down")
    logger.info("=" * 70)
    
    # Close database connections
    if app_state["db_engine"] is not None:
        logger.info("Closing database connections...")
        try:
            app_state["db_engine"].dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
    
    logger.info("=" * 70)
    logger.info("Application shutdown complete")
    logger.info("=" * 70)


# Initialize FastAPI application with lifespan
app = FastAPI(
    title="TraceBrain Tracing API",
    description="Observability platform for Agentic AI - Collect, store, and visualize execution traces",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    logger.error("Unhandled exception", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# ============================================================================
# CORS Middleware Configuration
# ============================================================================
# Allow all origins for development - restrict in production
allow_all = "*" in settings.CORS_ALLOW_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ============================================================================
# API Router Registration
# ============================================================================
# Mount the v1 API router under /api/v1 prefix
app.include_router(
    api_v1_router,
    prefix="/api/v1",
    tags=["API v1"]
)

# ============================================================================
# Static Files & Frontend Serving
# ============================================================================
# Determine the path to the static directory
# This enables the "pip install and run" experience where React build
# artifacts are served by the Python backend

# Get the package root directory
package_dir = Path(__file__).parent
static_dir = package_dir / settings.STATIC_DIR

logger.info(f"Package directory: {package_dir}")
logger.info(f"Looking for static files in: {static_dir}")

# Mount static files if the directory exists
if static_dir.exists() and static_dir.is_dir():
    logger.info("Static directory found, mounting React frontend at /")
    
    # Mount static files (JS, CSS, images, etc.)
    app.mount(
        "/static",
        StaticFiles(directory=str(static_dir)),
        name="static"
    )
    
    # Serve index.html for the root path and SPA routes
    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        """Serve the React frontend index.html"""
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Frontend not built yet - static files found but index.html missing"}
    
    # Catch-all route for SPA routing (must be last)
    # This ensures React Router can handle client-side routing
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Serve React app for all non-API routes (SPA routing)"""
        # Don't intercept API routes
        if full_path.startswith("api/"):
            return {"error": "Not found"}
        
        # Check if it's a static file request
        file_path = static_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        # Otherwise, serve index.html for SPA routing
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"error": "Not found"}
    
else:
    logger.warning(f"Static directory not found: {static_dir}")
    logger.warning("  Frontend will not be served. API endpoints are still available.")
    logger.warning("  To enable frontend, build the React app and place files in:")
    logger.warning(f"  {static_dir}")
    
    # Provide a helpful message at the root
    @app.get("/", include_in_schema=False)
    async def root_message():
        """Root endpoint when frontend is not available"""
        return {
            "message": "TraceBrain Tracing API",
            "version": "1.0.0",
            "status": "API only (frontend not built)",
            "api_docs": "/docs",
            "api_base": "/api/v1"
        }

# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/healthz", tags=["System"])
async def healthz():
    """
    Kubernetes-style health check endpoint.
    
    Returns a simple OK status to verify the application is running.
    """
    return {"status": "ok"}
