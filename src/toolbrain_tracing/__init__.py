"""
ToolBrain Tracing - Observability Platform for Agentic AI

This package provides a complete observability solution for AI agents,
allowing users to collect, store, and visualize execution traces.

Philosophy: "Pip install and run"
- Single package containing both backend (FastAPI) and frontend (React)
- Support for SQLite (development) and PostgreSQL (production)
- Custom ToolBrain Standard OTLP Trace Schema
- Robust SDK client with automatic retries and fail-safe design

Quick Start:
    # Install
    pip install toolbrain-tracing
    
    # Start infrastructure with Docker (recommended)
    toolbrain-trace up
    
    # Or use Python server directly for development
    toolbrain-trace init-db
    toolbrain-trace start
    
    # Use the SDK client in your code
    from toolbrain_tracing import TraceClient
    
    client = TraceClient()
    success = client.log_trace({
        "trace_id": "abc123",
        "attributes": {"system_prompt": "You are helpful"},
        "spans": [...]
    })

Usage:
    # Import the FastAPI app
    from toolbrain_tracing import app
    
    # Import configuration
    from toolbrain_tracing import settings
    
    # Import SDK client (recommended)
    from toolbrain_tracing import TraceClient
    
    # Import TraceStore for programmatic access
    from toolbrain_tracing.core.store import TraceStore
"""

__version__ = "2.0.0"
__author__ = "ToolBrain Team"

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
