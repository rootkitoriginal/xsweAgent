# Configuration Module (`src/config/`)

## Purpose
Centralized configuration management using Pydantic V2 for validation and environment variables.

## Key Components

### Settings (`settings.py`)
```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class GitHubSettings(BaseModel):
    """GitHub API configuration."""
    token: str = Field(..., description="GitHub API token")
    repo_name: str = Field(..., pattern=r"^[\w-]+/[\w-]+$")
    base_url: str = "https://api.github.com"

class GeminiSettings(BaseModel):
    """Gemini API configuration."""
    api_key: str = Field(..., description="Google Gemini API key")
    model_name: str = "gemini-2.5-flash"

class Settings(BaseSettings):
    """Main application settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__"
    )
    
    github: GitHubSettings
    gemini: GeminiSettings
    log_level: str = "INFO"

def get_config() -> Settings:
    """Get application settings (singleton)."""
    return Settings()
```

## Environment Variables

### Naming Convention
```bash
# Nested configuration
GITHUB__TOKEN=ghp_xxx
GITHUB__REPO_NAME=owner/repo
GEMINI__API_KEY=xxx
LOG_LEVEL=DEBUG
```

### .env File
```env
# GitHub Configuration
GITHUB__TOKEN=your_token_here
GITHUB__REPO_NAME=owner/repo

# Gemini Configuration
GEMINI__API_KEY=your_api_key_here

# Application
LOG_LEVEL=INFO
```

## Logging Configuration (`logging_config.py`)

### Setup
```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(log_level: str = "INFO"):
    """Configure application logging."""
    logger = logging.getLogger("xswe_agent")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(
        logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
    )
    logger.addHandler(console)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        "logs/xswe_agent.log",
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s'
        )
    )
    logger.addHandler(file_handler)
    
    return logger
```

### Usage
```python
from src.config import setup_logging, get_config

settings = get_config()
logger = setup_logging(settings.log_level)

logger.info("Application started")
logger.debug(f"Config: {settings.github.repo_name}")
logger.error("Error occurred", exc_info=True)
```

## Validation

### Field Validators
```python
from pydantic import field_validator

class Settings(BaseSettings):
    port: int = 8000
    
    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        if not 1024 <= v <= 65535:
            raise ValueError("Port must be between 1024 and 65535")
        return v
```

### Model Validators
```python
from pydantic import model_validator

class DatabaseSettings(BaseModel):
    host: str
    port: int
    
    @model_validator(mode="after")
    def validate_connection(self):
        # Custom validation logic
        return self
```

## Best Practices

### Secrets Management
- Never commit `.env` files
- Use environment variables in production
- Mask sensitive values in logs
- Use separate configs for dev/test/prod

### Type Safety
```python
# Use proper types
cache_ttl: int = 300  # seconds
enable_feature: bool = False
allowed_origins: List[str] = ["http://localhost:3000"]
```

### Documentation
```python
class Settings(BaseSettings):
    """Application settings.
    
    Environment variables use double underscore for nesting:
    - GITHUB__TOKEN: GitHub API token
    - GEMINI__API_KEY: Gemini API key
    """
    pass
```

## Testing
```python
def test_settings_validation():
    """Test settings validation."""
    with pytest.raises(ValueError):
        GitHubSettings(
            token="invalid",
            repo_name="invalid-format"  # Missing owner/
        )

def test_env_loading(monkeypatch):
    """Test loading from environment."""
    monkeypatch.setenv("GITHUB__TOKEN", "test_token")
    monkeypatch.setenv("GITHUB__REPO_NAME", "owner/repo")
    
    settings = get_config()
    assert settings.github.token == "test_token"
```
