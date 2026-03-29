"""
TraceBrain Configuration Module

This module provides centralized configuration management using pydantic-settings.
It handles environment variables, defaults, and configuration validation.

Usage:
    from tracebrain.config import settings
    
    print(settings.DATABASE_URL)
    app.run(host=settings.HOST, port=settings.PORT)
"""

from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator

load_dotenv()


class Settings(BaseSettings):
    """
    Application settings and configuration.
    
    Configuration is loaded from environment variables with fallback to defaults.
    The .env file is automatically loaded if present in the working directory.
    
    Attributes:
        DATABASE_URL: SQLAlchemy database connection string.
            - SQLite (default): "sqlite:///./tracebrain_traces.db"
            - PostgreSQL: "postgresql://user:password@host/database"
        HOST: Server host address (default: "127.0.0.1")
        PORT: Server port number (default: 8000)
        LOG_LEVEL: Logging level (default: "info")
        LLM provider API keys are provider-specific and loaded from env variables
            (OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY, HUGGINGFACE_API_KEY)
        STATIC_DIR: Path to static files directory (for React frontend)
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="sqlite:///./tracebrain_traces.db",
        description="Database connection URL (SQLite or PostgreSQL)"
    )
    
    # Server Configuration
    HOST: str = Field(
        default="127.0.0.1",
        description="Server host address"
    )
    
    PORT: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port number"
    )
    
    LOG_LEVEL: str = Field(
        default="info",
        description="Logging level (debug, info, warning, error, critical)"
    )

    # Database Pool Configuration
    DB_POOL_SIZE: int = Field(
        default=10,
        ge=1,
        description="Base number of database connections in the pool"
    )
    DB_MAX_OVERFLOW: int = Field(
        default=20,
        ge=0,
        description="Maximum number of overflow connections beyond pool size"
    )
    DB_POOL_RECYCLE: int = Field(
        default=1800,
        ge=60,
        description="Recycle DB connections after N seconds"
    )
    
    # Embedding Configuration
    EMBEDDING_PROVIDER: str = Field(
        default="local",
        description="Embedding provider (local, openai, gemini, none)"
    )
    EMBEDDING_MODEL: str = Field(
        default="all-MiniLM-L6-v2",
        description="Embedding model name for local provider"
    )
    EMBEDDING_API_KEY: Optional[str] = Field(
        default=None,
        description="API key for embedding provider (if required)"
    )
    EMBEDDING_BASE_URL: Optional[str] = Field(
        default=None,
        description="Base URL for embedding provider (OpenAI-compatible)"
    )

    # LLM runtime mode + legacy fallback route defaults
    LIBRARIAN_MODE: str = Field(
        default="api",
        description="Runtime mode: api or open_source"
    )
    LLM_PROVIDER: str = Field(
        default="gemini",
        description="Legacy fallback provider when DB runtime settings are unavailable"
    )
    LLM_MODEL: str = Field(
        default="gemini-2.5-flash",
        description="Legacy fallback model when DB runtime settings are unavailable"
    )
    LLM_BASE_URL: Optional[str] = Field(
        default=None,
        description="Optional fallback base URL for open-source/openai-compatible providers"
    )
    HUGGINGFACE_BASE_URL: Optional[str] = Field(
        default=None,
        description="Base URL for Hugging Face-compatible inference endpoint (e.g., vLLM/TGI proxy)"
    )
    LLM_TEMPERATURE: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="LLM sampling temperature"
    )
    LLM_MAX_TOKENS: Optional[int] = Field(
        default=None,
        ge=1,
        description="Max tokens for LLM response"
    )
    LLM_TIMEOUT: int = Field(
        default=30,
        ge=5,
        description="LLM request timeout (seconds)"
    )
    LLM_DEBUG: bool = Field(
        default=False,
        description="Enable verbose logging for LLM tool calls and responses"
    )

    AUTO_EVALUATE_TRACES: bool = Field(
        default=True,
        description="Automatically run AI evaluation on ingested traces"
    )
    
    # Frontend Configuration
    STATIC_DIR: str = Field(
        default="static",
        description="Directory containing React build artifacts (relative to package root)"
    )

    # CORS Configuration
    CORS_ALLOW_ORIGINS: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed CORS origins (comma-separated string or JSON list)"
    )

    @field_validator("CORS_ALLOW_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value):
        if isinstance(value, str):
            cleaned = [v.strip() for v in value.split(",") if v.strip()]
            return cleaned or ["*"]
        return value

    @model_validator(mode="after")
    def _validate_required_keys(self):
        embedding_provider = (self.EMBEDDING_PROVIDER or "").lower()
        if embedding_provider in {"openai", "gemini"} and not self.EMBEDDING_API_KEY:
            raise ValueError(
                "EMBEDDING_API_KEY is required when EMBEDDING_PROVIDER is openai or gemini."
            )

        return self
    
    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return self.DATABASE_URL.startswith("sqlite")
    
    @property
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL database."""
        return self.DATABASE_URL.startswith("postgresql")
    
    def get_backend_type(self) -> str:
        """
        Determine the storage backend type from DATABASE_URL.
        
        Returns:
            str: "sqlite" or "postgres"
        """
        if self.is_sqlite:
            return "sqlite"
        elif self.is_postgres:
            return "postgres"
        else:
            # Default to sqlite for unknown/unsupported backends
            return "sqlite"


# Global settings instance
# Import this throughout the application
settings = Settings()
