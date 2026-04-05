"""
TraceBrain Command-Line Interface

This module provides a CLI for managing the TraceBrain service.
It allows users to start the API server, manage the database, perform
administrative tasks, and orchestrate Docker infrastructure.

Usage:
    # Docker orchestration (recommended for production)
    tracebrain up              # Start infrastructure with Docker
    # If code changes are not picked up by Docker, rebuild without cache:
    #   docker compose -f docker/docker-compose.yml build --no-cache
    #   tracebrain up
    tracebrain down            # Stop infrastructure
    tracebrain status          # Check container status
    
    # Development mode (local Python server)
    tracebrain start           # Start Python server directly
    tracebrain start --host 0.0.0.0 --port 3000
    
    # Database management
    tracebrain init            # Create a local .env template
    tracebrain init-db         # Initialize database tables
    
    # System information
    tracebrain info            # Show current configuration
"""

import sys
import subprocess
import time
import os
from pathlib import Path
from typing import Optional
import typer

from .config import settings

# Create Typer app
app = typer.Typer(
    name="tracebrain",
    help="TraceBrain - Trace management and observability for LLM-based agents",
    add_completion=False
)


# ============================================================================
# Helper Functions
# ============================================================================

def find_docker_compose_file() -> Optional[Path]:
    """
    Locate the docker-compose.yml file in the package.

    Returns:
        Optional[Path]: Path to docker-compose.yml if found, None otherwise
    """
    compose_file = Path(__file__).resolve().parent / "resources" / "docker" / "docker-compose.yml"
    return compose_file if compose_file.is_file() else None


def get_user_env_file() -> Path:
    """
    Get the user project .env file from the current working directory.

    Returns:
        Path: The expected .env path in current working directory.
    """
    return Path.cwd() / ".env"


def build_compose_base_command(compose_file: Path, env_file: Path) -> list[str]:
    """
    Build the base docker compose command and inject --env-file when available.

    Args:
        compose_file: Path to docker-compose.yml bundled with the package
        env_file: User .env file path in current working directory

    Returns:
        list[str]: Base command parts for docker compose invocation
    """
    cmd = ["docker", "compose", "-f", str(compose_file)]
    if env_file.exists():
        cmd.extend(["--env-file", str(env_file)])
    return cmd


def check_docker_installed() -> bool:
    """
    Check if Docker is installed and accessible.
    
    Returns:
        bool: True if docker command is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def wait_for_health_check(
    base_url: str = "http://localhost:8000",
    timeout: int = 60,
    interval: int = 2
) -> bool:
    """
    Wait for the TraceStore API to become healthy.
    
    Args:
        base_url: Base URL of the API
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
    
    Returns:
        bool: True if API became healthy, False if timeout
    """
    from .sdk.client import TraceClient
    
    client = TraceClient(base_url=base_url)
    start_time = time.time()
    
    typer.echo(f"Waiting for TraceStore to become ready at {base_url}...")
    
    while time.time() - start_time < timeout:
        if client.health_check():
            typer.echo("TraceStore is ready")
            return True
        
        time.sleep(interval)
        typer.echo(".", nl=False)  # Progress indicator
    
    typer.echo("\nTimeout waiting for TraceStore to become ready")
    return False


# ============================================================================
# Docker Orchestration Commands
# ============================================================================

@app.command()
def init():
    """Create a local .env template in the current working directory."""
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        typer.echo(".env already exists in the current directory.")
        return

    template = """# TraceBrain Configuration
# Copy this file to .env and customize as needed

# --- DATABASE CONFIGURATION ---
# SQLite (default for development)
DATABASE_URL=sqlite:///./tracebrain_traces.db

# PostgreSQL (for production)
# DATABASE_URL=postgresql://tracebrain:tracebrain_2026_secure@localhost:5432/tracestore
POSTGRES_USER=tracebrain
POSTGRES_PASSWORD=tracebrain_2026_secure
POSTGRES_DB=tracestore

# --- SERVER CONFIGURATION ---
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=info

# --- LLM API KEYS (Key infrastructure) ---
# Users should enter all API keys they own here once.
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
# ANTHROPIC_API_KEY=your_claude_api_key_here
# HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# Optional provider endpoints/proxies
# OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
# ANTHROPIC_BASE_URL=https://your-anthropic-endpoint
# HUGGINGFACE_BASE_URL=http://localhost:8000

# --- BOOTSTRAP DEFAULTS (Default configuration before UI setup) ---
# These variables allow the system to start when the database is empty (first startup).
DEFAULT_LIBRARIAN_PROVIDER=openai
DEFAULT_LIBRARIAN_MODEL=gpt-4o-mini
DEFAULT_JUDGE_PROVIDER=gemini
DEFAULT_JUDGE_MODEL=gemini-2.5-flash
DEFAULT_CURATOR_PROVIDER=gemini
DEFAULT_CURATOR_MODEL=gemini-2.5-flash

# --- SYSTEM SETTINGS ---
LIBRARIAN_MODE=api
LLM_DEBUG=false

# --- DOCKER IMAGE PROFILE (Optional) ---
# TRACEBRAIN_IMAGE=quyk67uet/tracebrain:latest
# TRACEBRAIN_IMAGE=quyk67uet/tracebrain:slim

# --- EMBEDDING SETTINGS ---
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-MiniLM-L6-v2
# EMBEDDING_API_KEY=your_embedding_api_key_here
# EMBEDDING_BASE_URL=https://your-embedding-endpoint/v1
"""

    env_path.write_text(template, encoding="utf-8")
    typer.echo(typer.style("Created .env in the current directory.", fg=typer.colors.GREEN, bold=True))
    typer.echo("Edit the .env file before running 'tracebrain up'.")

@app.command()
def up(
    build: bool = typer.Option(
        False,
        "--build",
        help="Rebuild images before starting"
    ),
    detach: bool = typer.Option(
        True,
        "--detach/--no-detach",
        "-d",
        help="Run containers in detached mode (background)"
    ),
    wait: bool = typer.Option(
        True,
        "--wait/--no-wait",
        help="Wait for health check after startup"
    ),
    slim: bool = typer.Option(
        False,
        "--slim",
        help="Use lightweight cloud-only image profile (quyk67uet/tracebrain:slim)"
    )
):
    """
    Start the TraceBrain infrastructure using Docker Compose.
    
    This command locates the docker-compose.yml file and starts all services
    (PostgreSQL database, FastAPI backend, etc.) in containers.
    
    Examples:
        tracebrain up                 # Start in background
        tracebrain up --slim          # Start lightweight cloud-first image
        tracebrain up --build         # Rebuild and start
        tracebrain up --no-detach     # Start in foreground (see logs)
        tracebrain up --no-wait       # Don't wait for health check
    """
    typer.echo("=" * 70)
    typer.echo("TraceBrain - Starting Infrastructure")
    typer.echo("=" * 70)
    
    # Check if Docker is installed
    if not check_docker_installed():
        typer.echo("Error: Docker is not installed or not in PATH", err=True)
        typer.echo("")
        typer.echo("Please install Docker:")
        typer.echo("  - Windows/Mac: https://www.docker.com/products/docker-desktop")
        typer.echo("  - Linux: https://docs.docker.com/engine/install/")
        typer.echo("")
        sys.exit(1)
    
    # Find docker-compose.yml
    compose_file = find_docker_compose_file()
    if not compose_file:
        typer.echo("Error: docker-compose.yml not found", err=True)
        typer.echo("")
        typer.echo("Expected path:")
        typer.echo("  - tracebrain/resources/docker/docker-compose.yml")
        typer.echo("")
        typer.echo("Please ensure the packaged resources are present.")
        sys.exit(1)
    
    env_file = get_user_env_file()

    typer.echo(f"Using: {compose_file}")
    if env_file.exists():
        typer.echo(f"Env file: {env_file}")
    else:
        typer.secho(
            "Warning: No .env found in current directory. Run 'tracebrain init' first.",
            fg=typer.colors.YELLOW,
        )
    typer.echo("")
    
    # Build docker compose command
    cmd = build_compose_base_command(compose_file, env_file)
    cmd.append("up")
    
    if build:
        cmd.append("--build")
    
    if detach:
        cmd.append("-d")

    compose_runtime_env = os.environ.copy()
    if slim:
        compose_runtime_env["TRACEBRAIN_IMAGE"] = "quyk67uet/tracebrain:slim"
        typer.secho(
            "Using slim image profile: quyk67uet/tracebrain:slim (cloud embedding recommended)",
            fg=typer.colors.CYAN,
        )
    
    typer.echo(f"Running: {' '.join(cmd)}")
    typer.echo("")
    
    # Execute docker compose up
    try:
        result = subprocess.run(
            cmd,
            check=True,
            text=True,
            env=compose_runtime_env,
        )
        
        if result.returncode == 0:
            typer.echo("")
            typer.echo("Infrastructure started successfully")
            typer.echo("")
            
            # Wait for health check if in detached mode and wait is enabled
            if detach and wait:
                if wait_for_health_check():
                    typer.echo("")
                    typer.echo("TraceBrain is ready")
                    typer.echo("")
                    typer.echo("Next steps:")
                    typer.echo("  -> API docs:  http://localhost:8000/docs")
                    typer.echo("  -> Frontend:  http://localhost:8000/")
                    typer.echo("  -> Check status: tracebrain status")
                    logs_cmd = f"docker compose -f {compose_file}"
                    if env_file.exists():
                        logs_cmd += f" --env-file {env_file}"
                    logs_cmd += " logs -f"
                    typer.echo(f"  -> View logs: {logs_cmd}")
                    typer.echo("")
                else:
                    typer.echo("")
                    typer.echo("Warning: services started but health check timed out")
                    logs_cmd = f"docker compose -f {compose_file}"
                    if env_file.exists():
                        logs_cmd += f" --env-file {env_file}"
                    logs_cmd += " logs"
                    typer.echo(f"Check logs with: {logs_cmd}")
            
    except subprocess.CalledProcessError as e:
        typer.echo(f"\nError starting infrastructure: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        typer.echo("\n\nInterrupted by user")
        sys.exit(1)


@app.command()
def down(
    volumes: bool = typer.Option(
        False,
        "--volumes",
        "-v",
        help="Remove volumes (WARNING: deletes all data!)"
    )
):
    """
    Stop and remove the TraceBrain infrastructure.
    
    This command stops all Docker containers and removes them.
    By default, data volumes are preserved.
    
    Examples:
        tracebrain down           # Stop and remove containers
        tracebrain down --volumes # WARNING: Also delete data volumes
    """
    typer.echo("=" * 70)
    typer.echo("TraceBrain - Stopping Infrastructure")
    typer.echo("=" * 70)
    
    # Check if Docker is installed
    if not check_docker_installed():
        typer.echo("Error: Docker is not installed or not in PATH", err=True)
        sys.exit(1)
    
    # Find docker-compose.yml
    compose_file = find_docker_compose_file()
    if not compose_file:
        typer.echo("Error: docker-compose.yml not found", err=True)
        sys.exit(1)
    
    env_file = get_user_env_file()

    typer.echo(f"Using: {compose_file}")
    if env_file.exists():
        typer.echo(f"Env file: {env_file}")
    typer.echo("")
    
    # Confirm if volumes flag is used
    if volumes:
        typer.echo("WARNING: --volumes flag will DELETE ALL DATA!")
        confirm = typer.confirm("Are you sure you want to continue?")
        if not confirm:
            typer.echo("Aborted.")
            sys.exit(0)
        typer.echo("")
    
    # Build docker compose command
    cmd = build_compose_base_command(compose_file, env_file)
    cmd.append("down")
    
    if volumes:
        cmd.append("--volumes")
    
    typer.echo(f"Running: {' '.join(cmd)}")
    typer.echo("")
    
    # Execute docker compose down
    try:
        result = subprocess.run(
            cmd,
            check=True,
            text=True
        )
        
        if result.returncode == 0:
            typer.echo("")
            typer.echo("Infrastructure stopped successfully")
            if volumes:
                typer.echo("Data volumes removed")
            typer.echo("")
            
    except subprocess.CalledProcessError as e:
        typer.echo(f"\nError stopping infrastructure: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        typer.echo("\n\nInterrupted by user")
        sys.exit(1)


@app.command()
def seed():
    """Seed the database with bundled sample traces if empty."""
    from .core.store import TraceStore
    from .core.seeder import seed_if_empty

    store = TraceStore(backend=settings.get_backend_type(), db_url=settings.DATABASE_URL)
    seed_if_empty(store)
    typer.echo("Seeding complete (or skipped if traces already exist).")


@app.command()
def status():
    """
    Check the status of TraceBrain Docker containers.
    
    This command shows which containers are running, their status,
    and port mappings.
    
    Example:
        tracebrain status
    """
    typer.echo("=" * 70)
    typer.echo("TraceBrain - Container Status")
    typer.echo("=" * 70)
    typer.echo("")
    
    # Check if Docker is installed
    if not check_docker_installed():
        typer.echo("Error: Docker is not installed or not in PATH", err=True)
        sys.exit(1)
    
    # Find docker-compose.yml
    compose_file = find_docker_compose_file()
    if not compose_file:
        typer.echo("Error: docker-compose.yml not found", err=True)
        sys.exit(1)

    env_file = get_user_env_file()

    typer.echo(f"Using: {compose_file}")
    if env_file.exists():
        typer.echo(f"Env file: {env_file}")
    typer.echo("")
    
    # Build docker compose command
    cmd = build_compose_base_command(compose_file, env_file)
    cmd.append("ps")
    
    # Execute docker compose ps
    try:
        subprocess.run(cmd, check=True)
        typer.echo("")
        
    except subprocess.CalledProcessError as e:
        typer.echo(f"\nError checking status: {e}", err=True)
        sys.exit(1)


# ============================================================================
# Development Server Commands
# ============================================================================


@app.command()
def start(
    host: Optional[str] = typer.Option(
        None,
        "--host",
        "-h",
        help="Host to bind the server to (overrides config)"
    ),
    port: Optional[int] = typer.Option(
        None,
        "--port",
        "-p",
        help="Port to bind the server to (overrides config)"
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        help="Enable auto-reload for development"
    ),
    log_level: Optional[str] = typer.Option(
        None,
        "--log-level",
        help="Logging level (debug, info, warning, error, critical)"
    ),
    workers: int = typer.Option(
        1,
        "--workers",
        "-w",
        help="Number of worker processes (default: 1)",
    )
):
    """
    Start the TraceBrain API server.
    
    This command starts the FastAPI server with uvicorn. The server will
    serve both the REST API and the React frontend (if built).
    
    Examples:
        tracebrain start
        tracebrain start --host 0.0.0.0 --port 8080
        tracebrain start --reload --log-level debug
    """
    # Use provided values or fall back to settings
    server_host = host or settings.HOST
    server_port = port or settings.PORT
    server_log_level = (log_level or settings.LOG_LEVEL).lower()
    
    typer.echo("=" * 70)
    typer.echo("TraceBrain - Starting API Server")
    typer.echo("=" * 70)
    typer.echo(f"Host:           {server_host}")
    typer.echo(f"Port:           {server_port}")
    typer.echo(f"Database:       {settings.DATABASE_URL}")
    typer.echo(f"Backend Type:   {settings.get_backend_type()}")
    typer.echo(f"Log Level:      {server_log_level}")
    typer.echo(f"Reload:         {reload}")
    typer.echo(f"Workers:        {workers}")
    typer.echo("")
    typer.echo(f"-> API Docs:     http://{server_host}:{server_port}/docs")
    typer.echo(f"-> Frontend:     http://{server_host}:{server_port}/")
    typer.echo("=" * 70)
    typer.echo("")
    
    try:
        import uvicorn

        uvicorn.run(
            "tracebrain.main:app",
            host=server_host,
            port=server_port,
            reload=reload,
            log_level=server_log_level,
            workers=workers,
        )
    except KeyboardInterrupt:
        typer.echo("\n\nServer stopped by user")
    except Exception as e:
        typer.echo(f"\nError starting server: {e}", err=True)
        sys.exit(1)


@app.command()
def init_db(
    drop_existing: bool = typer.Option(
        False,
        "--drop",
        help="Drop existing tables before creating (WARNING: Deletes all data!)"
    )
):
    """
    Initialize the database by creating all required tables.
    
    This command creates the necessary database tables (traces, spans, etc.)
    based on the SQLAlchemy models. It's safe to run multiple times as it
    only creates tables that don't exist.
    
    Examples:
        tracebrain init-db
        tracebrain init-db --drop  # WARNING: Deletes all data!
    """
    from .db.session import create_tables, drop_tables
    from .core.store import TraceStore
    from .core.seeder import seed_data
    
    typer.echo("=" * 70)
    typer.echo("TraceBrain - Database Initialization")
    typer.echo("=" * 70)
    typer.echo(f"Database:       {settings.DATABASE_URL}")
    typer.echo(f"Backend Type:   {settings.get_backend_type()}")
    typer.echo("")
    
    if drop_existing:
        typer.echo("WARNING: Dropping existing tables (all data will be lost)...")
        confirm = typer.confirm("Are you sure you want to continue?")
        if not confirm:
            typer.echo("Aborted.")
            sys.exit(0)
        
        try:
            drop_tables()
            typer.echo("Existing tables dropped")
        except Exception as e:
            typer.echo(f"Error dropping tables: {e}", err=True)
            sys.exit(1)
    
    try:
        create_tables()
        typer.echo("Database tables created successfully")
        typer.echo("")
        store = TraceStore(backend=settings.get_backend_type(), db_url=settings.DATABASE_URL)
        existing = store.count_traces()
        if existing == 0:
            prompt = typer.style(
                "Database is empty. Would you like to seed 20 sample traces for a better initial experience?",
                fg=typer.colors.GREEN,
                bold=True,
            )
            if typer.confirm(prompt):
                seed_data(store)
            else:
                typer.echo("Skipping sample ingestion. Your TraceStore is ready for clean data.")
        typer.echo("You can now start the server with: tracebrain start")
    except Exception as e:
        typer.echo(f"Error creating tables: {e}", err=True)
        sys.exit(1)


@app.command()
def generate_curriculum():
    """
    Generate curriculum tasks from failed traces.

    Example:
        tracebrain generate-curriculum
    """
    from .core.curator import CurriculumCurator
    from .core.store import TraceStore

    typer.echo("=" * 70)
    typer.echo("TraceBrain - Curriculum Generation")
    typer.echo("=" * 70)
    typer.echo(f"Database:       {settings.DATABASE_URL}")
    typer.echo(f"Backend Type:   {settings.get_backend_type()}")
    typer.echo("")

    store = TraceStore(
        backend=settings.get_backend_type(),
        db_url=settings.DATABASE_URL,
    )
    curator = CurriculumCurator(store)

    try:
        created = curator.generate_curriculum()
        typer.echo(f"Curriculum tasks generated: {created}")
    except Exception as e:
        typer.echo(f"Error generating curriculum: {e}", err=True)
        sys.exit(1)


@app.command()
def info():
    """
    Display current configuration and system information.
    
    This command shows the current configuration settings, including
    database connection, server settings, and available features.
    
    Example:
        tracebrain info
    """
    import platform
    from pathlib import Path
    
    typer.echo("=" * 70)
    typer.echo("TraceBrain - System Information")
    typer.echo("=" * 70)
    typer.echo("")
    
    typer.echo("[Configuration]")
    typer.echo(f"  Database URL:     {settings.DATABASE_URL}")
    typer.echo(f"  Backend Type:     {settings.get_backend_type()}")
    typer.echo(f"  Server Host:      {settings.HOST}")
    typer.echo(f"  Server Port:      {settings.PORT}")
    typer.echo(f"  Log Level:        {settings.LOG_LEVEL}")
    typer.echo(f"  Static Dir:       {settings.STATIC_DIR}")
    typer.echo("")
    
    typer.echo("[Features]")
    typer.echo(f"  Librarian Mode:   {settings.LIBRARIAN_MODE}")
    typer.echo(f"  Fallback Provider:{settings.LLM_PROVIDER}")
    typer.echo(f"  Fallback Model:   {settings.LLM_MODEL}")
    typer.echo(
        "  Provider Keys:    "
        f"openai={'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}, "
        f"gemini={'Yes' if os.getenv('GEMINI_API_KEY') else 'No'}, "
        f"anthropic={'Yes' if os.getenv('ANTHROPIC_API_KEY') else 'No'}, "
        f"huggingface={'Yes' if os.getenv('HUGGINGFACE_API_KEY') else 'No'}"
    )
    typer.echo("")
    
    # Check if static files exist
    package_dir = Path(__file__).parent
    static_dir = package_dir / settings.STATIC_DIR
    has_frontend = static_dir.exists() and (static_dir / "index.html").exists()
    
    typer.echo(f"  Frontend:         {'Available' if has_frontend else 'Not built'}")
    if not has_frontend:
        typer.echo(f"                    (Place React build in: {static_dir})")
    typer.echo("")
    
    typer.echo("[System]")
    typer.echo(f"  Python Version:   {platform.python_version()}")
    typer.echo(f"  Platform:         {platform.platform()}")
    typer.echo("")
    
    typer.echo("[Quick Start]")
    typer.echo("  1. Initialize database:  tracebrain init-db")
    typer.echo("  2. Start server:         tracebrain start")
    typer.echo("  3. Open browser:         http://localhost:8000/docs")
    typer.echo("")


@app.command()
def version():
    """
    Display the TraceBrain version.
    
    Example:
        tracebrain version
    """
    typer.echo("TraceBrain v1.0.0")


def main():
    """
    Main entry point for the CLI.
    
    This function is called when the user runs the 'tracebrain' command.
    It's registered as a console script entry point in setup.py/pyproject.toml.
    """
    app()


if __name__ == "__main__":
    main()
