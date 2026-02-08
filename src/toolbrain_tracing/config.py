"""
ToolBrain Tracing Configuration Module

This module provides centralized configuration management using pydantic-settings.
It handles environment variables, defaults, and configuration validation.

Usage:
    from toolbrain_tracing.config import settings
    
    print(settings.DATABASE_URL)
    app.run(host=settings.HOST, port=settings.PORT)
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """
    Application settings and configuration.
    
    Configuration is loaded from environment variables with fallback to defaults.
    The .env file is automatically loaded if present in the working directory.
    
    Attributes:
        DATABASE_URL: SQLAlchemy database connection string.
            - SQLite (default): "sqlite:///./toolbrain_traces.db"
            - PostgreSQL: "postgresql://user:password@host/database"
        HOST: Server host address (default: "127.0.0.1")
        PORT: Server port number (default: 8000)
        LOG_LEVEL: Logging level (default: "info")
        GEMINI_API_KEY: Optional API key for Gemini AI features
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
        default="sqlite:///./toolbrain_traces.db",
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
        default=5,
        ge=1,
        description="Base number of database connections in the pool"
    )
    DB_MAX_OVERFLOW: int = Field(
        default=10,
        ge=0,
        description="Maximum number of overflow connections beyond pool size"
    )
    DB_POOL_RECYCLE: int = Field(
        default=1800,
        ge=60,
        description="Recycle DB connections after N seconds"
    )
    
    # Optional Features
    GEMINI_API_KEY: Optional[str] = Field(
        default=None,
        description="Google Gemini API key for AI-powered query features"
    )

    # LLM Configuration (Librarian)
    LIBRARIAN_MODE: str = Field(
        default="api",
        description="LLM mode: api or open_source"
    )
    LLM_PROVIDER: str = Field(
        default="gemini",
        description="LLM provider (gemini, openai, azure_openai, anthropic, openai_compatible, huggingface, hf, ollama, vllm, tgi, lmstudio)"
    )
    LLM_MODEL: str = Field(
        default="gemini-2.5-flash",
        description="LLM model name"
    )
    LLM_API_KEY: Optional[str] = Field(
        default=None,
        description="API key for LLM provider (if required)"
    )
    LLM_BASE_URL: Optional[str] = Field(
        default=None,
        description="Base URL for LLM provider"
    )
    LLM_API_VERSION: Optional[str] = Field(
        default=None,
        description="API version for providers that require it (e.g., Azure)"
    )
    LLM_AZURE_DEPLOYMENT: Optional[str] = Field(
        default=None,
        description="Azure OpenAI deployment name"
    )
    LLM_ANTHROPIC_VERSION: str = Field(
        default="2023-06-01",
        description="Anthropic API version"
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
