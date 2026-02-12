"""
TraceBrain Tracing Command-Line Interface

This module provides a CLI for managing the TraceBrain Tracing service.
It allows users to start the API server, manage the database, perform
administrative tasks, and orchestrate Docker infrastructure.

Usage:
    # Docker orchestration (recommended for production)
    tracebrain-trace up              # Start infrastructure with Docker
    # If code changes are not picked up by Docker, rebuild without cache:
    #   docker compose -f docker/docker-compose.yml build --no-cache
    #   tracebrain-trace up
    tracebrain-trace down            # Stop infrastructure
    tracebrain-trace status          # Check container status
    
    # Development mode (local Python server)
    tracebrain-trace start           # Start Python server directly
    tracebrain-trace start --host 0.0.0.0 --port 3000
    
    # Database management
    tracebrain-trace init-db         # Initialize database tables
    
    # System information
    tracebrain-trace info            # Show current configuration
"""

import sys
import subprocess
import time
from pathlib import Path
from typing import Optional
import typer
import uvicorn

from .config import settings

# Create Typer app
app = typer.Typer(
    name="tracebrain-trace",
    help="TraceBrain Tracing - Observability platform for Agentic AI",
    add_completion=False
)


# ============================================================================
# Helper Functions
# ============================================================================

def find_docker_compose_file() -> Optional[Path]:
    """
    Locate the docker-compose.yml file in the package.
    
    Production standard: docker/docker-compose.yml in project root.
    This follows industry best practices for organizing infrastructure files.
    
    Returns:
        Optional[Path]: Path to docker-compose.yml if found, None otherwise
    """
    # Start from the current file location (cli.py)
    current_file = Path(__file__).resolve()
    
    # Try multiple locations (in order of preference)
    search_paths = [
        # 1. Project root docker/ directory (RECOMMENDED for production)
        current_file.parent.parent.parent / "docker" / "docker-compose.yml",
        
        # 2. Current working directory docker/
        Path.cwd() / "docker" / "docker-compose.yml",
        
        # 3. Legacy: same directory as cli.py (backward compatibility)
        current_file.parent / "docker-compose.yml",
        
        # 4. Legacy: project root (backward compatibility)
        current_file.parent.parent.parent / "docker-compose.yml",
        
        # 5. Fallback: current directory
        Path.cwd() / "docker-compose.yml",
    ]
    
    for path in search_paths:
        if path.exists() and path.is_file():
            return path
    
    return None


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
    )
):
    """
    Start the TraceBrain Tracing infrastructure using Docker Compose.
    
    This command locates the docker-compose.yml file and starts all services
    (PostgreSQL database, FastAPI backend, etc.) in containers.
    
    Examples:
        tracebrain-trace up                 # Start in background
        tracebrain-trace up --build         # Rebuild and start
        tracebrain-trace up --no-detach     # Start in foreground (see logs)
        tracebrain-trace up --no-wait       # Don't wait for health check
    """
    typer.echo("=" * 70)
    typer.echo("TraceBrain Tracing - Starting Infrastructure")
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
        typer.echo("Searched locations:")
        typer.echo("  - Project root directory")
        typer.echo("  - Package installation directory")
        typer.echo("")
        typer.echo("Please ensure docker-compose.yml exists in your project root.")
        sys.exit(1)
    
    typer.echo(f"Using: {compose_file}")
    typer.echo("")
    
    # Build docker compose command
    cmd = ["docker", "compose", "-f", str(compose_file), "up"]
    
    if build:
        cmd.append("--build")
    
    if detach:
        cmd.append("-d")
    
    typer.echo(f"Running: {' '.join(cmd)}")
    typer.echo("")
    
    # Execute docker compose up
    try:
        result = subprocess.run(
            cmd,
            check=True,
            text=True
        )
        
        if result.returncode == 0:
            typer.echo("")
            typer.echo("Infrastructure started successfully")
            typer.echo("")
            
            # Wait for health check if in detached mode and wait is enabled
            if detach and wait:
                if wait_for_health_check():
                    typer.echo("")
                    typer.echo("TraceBrain Tracing is ready")
                    typer.echo("")
                    typer.echo("Next steps:")
                    typer.echo("  -> API docs:  http://localhost:8000/docs")
                    typer.echo("  -> Frontend:  http://localhost:8000/")
                    typer.echo("  -> Check status: tracebrain-trace status")
                    typer.echo(f"  -> View logs: docker compose -f {compose_file} logs -f")
                    typer.echo("")
                else:
                    typer.echo("")
                    typer.echo("Warning: services started but health check timed out")
                    typer.echo(f"Check logs with: docker compose -f {compose_file} logs")
            
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
    Stop and remove the TraceBrain Tracing infrastructure.
    
    This command stops all Docker containers and removes them.
    By default, data volumes are preserved.
    
    Examples:
        tracebrain-trace down           # Stop and remove containers
        tracebrain-trace down --volumes # WARNING: Also delete data volumes
    """
    typer.echo("=" * 70)
    typer.echo("TraceBrain Tracing - Stopping Infrastructure")
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
    
    typer.echo(f"Using: {compose_file}")
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
    cmd = ["docker", "compose", "-f", str(compose_file), "down"]
    
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
def status():
    """
    Check the status of TraceBrain Tracing Docker containers.
    
    This command shows which containers are running, their status,
    and port mappings.
    
    Example:
        tracebrain-trace status
    """
    typer.echo("=" * 70)
    typer.echo("TraceBrain Tracing - Container Status")
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
    
    # Build docker compose command
    cmd = ["docker", "compose", "-f", str(compose_file), "ps"]
    
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
    )
):
    """
    Start the TraceBrain Tracing API server.
    
    This command starts the FastAPI server with uvicorn. The server will
    serve both the REST API and the React frontend (if built).
    
    Examples:
        tracebrain-trace start
        tracebrain-trace start --host 0.0.0.0 --port 8080
        tracebrain-trace start --reload --log-level debug
    """
    # Use provided values or fall back to settings
    server_host = host or settings.HOST
    server_port = port or settings.PORT
    server_log_level = (log_level or settings.LOG_LEVEL).lower()
    
    typer.echo("=" * 70)
    typer.echo("TraceBrain Tracing - Starting API Server")
    typer.echo("=" * 70)
    typer.echo(f"Host:           {server_host}")
    typer.echo(f"Port:           {server_port}")
    typer.echo(f"Database:       {settings.DATABASE_URL}")
    typer.echo(f"Backend Type:   {settings.get_backend_type()}")
    typer.echo(f"Log Level:      {server_log_level}")
    typer.echo(f"Reload:         {reload}")
    typer.echo("")
    typer.echo(f"-> API Docs:     http://{server_host}:{server_port}/docs")
    typer.echo(f"-> Frontend:     http://{server_host}:{server_port}/")
    typer.echo("=" * 70)
    typer.echo("")
    
    try:
        uvicorn.run(
            "tracebrain.main:app",
            host=server_host,
            port=server_port,
            reload=reload,
            log_level=server_log_level
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
        tracebrain-trace init-db
        tracebrain-trace init-db --drop  # WARNING: Deletes all data!
    """
    from .db.session import create_tables, drop_tables
    
    typer.echo("=" * 70)
    typer.echo("TraceBrain Tracing - Database Initialization")
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
        typer.echo("You can now start the server with: tracebrain-trace start")
    except Exception as e:
        typer.echo(f"Error creating tables: {e}", err=True)
        sys.exit(1)


@app.command()
def generate_curriculum():
    """
    Generate curriculum tasks from failed traces.

    Example:
        tracebrain-trace generate-curriculum
    """
    from .core.curator import CurriculumCurator
    from .core.store import TraceStore

    typer.echo("=" * 70)
    typer.echo("TraceBrain Tracing - Curriculum Generation")
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
        tracebrain-trace info
    """
    import platform
    from pathlib import Path
    
    typer.echo("=" * 70)
    typer.echo("TraceBrain Tracing - System Information")
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
    typer.echo(f"  LLM Provider:     {settings.LLM_PROVIDER}")
    typer.echo(f"  LLM API Key:      {'Configured' if settings.LLM_API_KEY else 'Missing'}")
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
    typer.echo("  1. Initialize database:  tracebrain-trace init-db")
    typer.echo("  2. Start server:         tracebrain-trace start")
    typer.echo("  3. Open browser:         http://localhost:8000/docs")
    typer.echo("")


@app.command()
def version():
    """
    Display the TraceBrain Tracing version.
    
    Example:
        tracebrain-trace version
    """
    typer.echo("TraceBrain Tracing v1.0.0")


def main():
    """
    Main entry point for the CLI.
    
    This function is called when the user runs the 'tracebrain-trace' command.
    It's registered as a console script entry point in setup.py/pyproject.toml.
    """
    app()


if __name__ == "__main__":
    main()
