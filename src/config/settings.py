"""
Configuration module for xSwE Agent.
Handles application settings, environment variables, and configuration management.
"""

from functools import lru_cache
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings as PydanticBaseSettings
import os
from pathlib import Path


class GitHubConfig(PydanticBaseSettings):
    """GitHub API configuration."""

    # Ensure environment variables are read directly during tests
    model_config = {"env_file": None, "case_sensitive": False}

    # Token made optional to allow the service to start in development
    # without immediate API credentials. Callers should validate presence
    # where external calls are made.
    token: Optional[str] = Field(
        None, env="GITHUB_TOKEN", description="GitHub personal access token"
    )
    # Allow either a single GITHUB_REPO env var (owner/name) or separate owner/name vars.
    repo: Optional[str] = Field(None, env="GITHUB_REPO")
    repo_owner: str = Field("xLabInternet", env="GITHUB_REPO_OWNER")
    repo_name: str = Field("xRatEcosystem", env="GITHUB_REPO_NAME")
    rate_limit_per_hour: int = Field(5000, env="GITHUB_RATE_LIMIT_PER_HOUR")

    @property
    def github_token(self) -> str:
        # allow direct env overrides for tests
        return self.token or os.getenv("GITHUB_TOKEN")

    @property
    def github_repo(self) -> str:
        # Prefer explicit GITHUB_REPO env var when present (owner/name)
        env_repo = os.getenv("GITHUB_REPO")
        if env_repo:
            return env_repo
        if self.repo:
            return self.repo
        return f"{self.repo_owner}/{self.repo_name}"


class GeminiConfig(PydanticBaseSettings):
    """Google Gemini AI configuration."""

    # Ensure environment variables are read directly during tests
    model_config = {"env_file": None, "case_sensitive": False}

    # API key optional to allow local development without immediate access
    api_key: Optional[str] = Field(
        None, env="GEMINI_API_KEY", description="Google Gemini API key"
    )
    model: str = Field("gemini-1.5-flash", env="GEMINI_MODEL")
    rate_limit_per_minute: int = Field(60, env="GEMINI_RATE_LIMIT_PER_MINUTE")

    @property
    def gemini_api_key(self) -> Optional[str]:
        return self.api_key or os.getenv("GEMINI_API_KEY")

    @property
    def gemini_model_name(self) -> str:
        return self.model

    @validator("api_key")
    def validate_api_key(cls, v):
        if not v:
            return v
        if v == "your_google_gemini_api_key_here":
            raise ValueError(
                "Please replace the placeholder Gemini API key in your environment."
            )
        return v


class MCPServerConfig(PydanticBaseSettings):
    """MCP Server configuration."""

    host: str = Field("0.0.0.0", env="MCP_SERVER_HOST")
    port: int = Field(8000, env="MCP_SERVER_PORT")
    debug: bool = Field(True, env="MCP_SERVER_DEBUG")
    cors_origins: str = Field("*", env="CORS_ORIGINS")

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


class CacheConfig(PydanticBaseSettings):
    """Cache configuration."""

    type: str = Field("memory", env="CACHE_TYPE")  # memory, redis, file
    ttl: int = Field(3600, env="CACHE_TTL")  # seconds
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")

    @validator("type")
    def validate_cache_type(cls, v):
        if v not in ["memory", "redis", "file"]:
            raise ValueError("Cache type must be: memory, redis, or file")
        return v


class AnalyticsConfig(PydanticBaseSettings):
    """Analytics configuration."""

    update_interval: int = Field(3600, env="ANALYTICS_UPDATE_INTERVAL")  # seconds
    history_days: int = Field(90, env="ANALYTICS_HISTORY_DAYS")
    chart_theme: str = Field("plotly_white", env="ANALYTICS_CHART_THEME")


class LoggingConfig(PydanticBaseSettings):
    """Logging configuration."""

    model_config = {"env_file": None, "case_sensitive": False}

    level: str = Field("INFO", env="LOG_LEVEL")
    format: str = Field("structured", env="LOG_FORMAT")  # structured, json, simple
    file: Optional[str] = Field("logs/xswe_agent.log", env="LOG_FILE")

    @validator("level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class SecurityConfig(PydanticBaseSettings):
    """Security configuration."""

    # Provide a development default to avoid failing startup in local/dev
    # environments. This MUST be overridden in production via env var.
    secret_key: str = Field("dev-change-me-please-0000000000000000", env="SECRET_KEY")
    api_key_expiration_hours: int = Field(24, env="API_KEY_EXPIRATION_HOURS")

    @validator("secret_key")
    def validate_secret_key(cls, v):
        if not v or v == "your-super-secret-key-change-this-in-production":
            raise ValueError("Valid secret key is required")
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v


class AppConfig(PydanticBaseSettings):
    """Main application configuration."""

    name: str = Field("xSweAgent", env="APP_NAME")
    version: str = Field("1.0.0", env="APP_VERSION")
    description: str = Field(
        "GitHub Issues Monitor & Analytics with Gemini AI", env="APP_DESCRIPTION"
    )
    debug: bool = Field(True, env="DEBUG")
    development_mode: bool = Field(True, env="DEVELOPMENT_MODE")

    # Sub-configurations
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    mcp_server: MCPServerConfig = Field(default_factory=MCPServerConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    analytics: AnalyticsConfig = Field(default_factory=AnalyticsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    # pydantic v2: use model_config for settings
    model_config = {
        # Avoid reading project .env automatically so test monkeypatching of
        # os.environ is authoritative during pytest runs.
        "env_file": None,
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        # Allow ignoring extra env vars at the top-level composition
        "extra": "ignore",
    }

    # --- Backwards-compatible property aliases (flattened names) ---
    @property
    def app_name(self) -> str:
        return self.name

    @property
    def app_version(self) -> str:
        return self.version

    @property
    def app_description(self) -> str:
        return self.description

    @property
    def log_level(self) -> str:
        return os.getenv("LOG_LEVEL") or self.logging.level

    @property
    def github_token(self) -> Optional[str]:
        return self.github.token

    @property
    def github_repo(self) -> str:
        # return combined owner/name for legacy callers
        return f"{self.github.repo_owner}/{self.github.repo_name}"

    @property
    def gemini_api_key(self) -> Optional[str]:
        return self.gemini.api_key

    @property
    def gemini_model_name(self) -> str:
        return self.gemini.model

    @property
    def port(self) -> int:
        return self.mcp_server.port

    @property
    def cors_origins(self) -> str:
        # Legacy callers expect a comma-separated string or '*'
        # There's no dedicated field in the nested config, so read env var
        # or return the permissive default.
        return os.getenv("CORS_ORIGINS", "*")


@lru_cache()
def get_settings() -> AppConfig:
    """Get cached application configuration. Kept name `get_settings` for
    compatibility with other modules that import `get_settings`.
    """
    return AppConfig()


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def ensure_directories():
    """Ensure required directories exist."""
    project_root = get_project_root()
    directories = [
        project_root / "logs",
        project_root / "data",
        project_root / "cache",
        project_root / "exports",
    ]

    for directory in directories:
        directory.mkdir(exist_ok=True)


# Initialize directories on module import
ensure_directories()
