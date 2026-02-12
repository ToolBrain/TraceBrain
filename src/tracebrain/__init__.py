"""
TraceBrain Tracing - Observability Platform for Agentic AI

This package provides a complete observability solution for AI agents,
allowing users to collect, store, and visualize execution traces.

Philosophy: "Pip install and run"
- Single package containing both backend (FastAPI) and frontend (React)
- Support for SQLite (development) and PostgreSQL (production)
- Custom TraceBrain Standard OTLP Trace Schema
- Robust SDK client with automatic retries and fail-safe design

Quick Start:
    # Install
    pip install tracebrain-tracing
    
    # Start infrastructure with Docker (recommended)
    tracebrain-trace up
    
    # Or use Python server directly for development
    tracebrain-trace init-db
    tracebrain-trace start
    
    # Use the SDK client in your code
    from tracebrain import TraceClient
    
    client = TraceClient()
    success = client.log_trace({
        "trace_id": "abc123",
        "attributes": {"system_prompt": "You are helpful"},
        "spans": [...]
    })

Usage:
    # Import the FastAPI app
    from tracebrain import app
    
    # Import configuration
    from tracebrain import settings
    
    # Import SDK client (recommended)
    from tracebrain import TraceClient
    
    # Import TraceStore for programmatic access
    from tracebrain.core.store import TraceStore
"""

__version__ = "1.0.0"
__author__ = "TraceBrain Team"

# Expose main components for easy import
from .main import app
from .config import settings
from .sdk import TraceClient

__all__ = [
    "app",
    "settings",
    "TraceClient",
    "__version__",
]
