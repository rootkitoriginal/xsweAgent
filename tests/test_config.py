"""
Tests for the configuration system.
"""

import os

import pytest
from pydantic import ValidationError

from src.config.settings import (AppConfig, GeminiConfig, GitHubConfig,
                                 MCPServerConfig, get_settings)


def test_app_config_defaults():
    """Test AppConfig default values."""
    config = AppConfig()
    assert config.app_name == "xSweAgent"
    assert config.log_level == "INFO"


def test_github_config_env_vars(monkeypatch):
    """Test GitHubConfig loading from environment variables."""
    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    monkeypatch.setenv("GITHUB_REPO", "test/repo")

    config = GitHubConfig()
    assert config.github_token == "test_token"
    assert config.github_repo == "test/repo"


def test_github_config_missing_vars():
    """Test GitHubConfig raises error if required variables are missing."""
    with pytest.raises(ValidationError):
        GitHubConfig()


def test_gemini_config_env_vars(monkeypatch):
    """Test GeminiConfig loading from environment variables."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_api_key")

    config = GeminiConfig()
    assert config.gemini_api_key == "test_api_key"
    assert config.gemini_model_name == "gemini-1.5-flash"


def test_mcp_server_config_defaults():
    """Test MCPServerConfig default values."""
    config = MCPServerConfig()
    assert config.host == "0.0.0.0"
    assert config.port == 8000
    assert config.cors_origins == "*"


def test_get_settings_caching():
    """Test that get_settings function caches the settings object."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


def test_settings_composition(monkeypatch):
    """Test that the main settings object correctly composes all configs."""
    monkeypatch.setenv("GITHUB_TOKEN", "gh_token")
    monkeypatch.setenv("GITHUB_REPO", "gh/repo")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini_key")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = get_settings()
    # Clear cache for re-loading
    get_settings.cache_clear()
    settings = get_settings()

    assert settings.app_name == "xSweAgent"
    assert settings.log_level == "DEBUG"
    assert settings.github_token == "gh_token"
    assert settings.github_repo == "gh/repo"
    assert settings.gemini_api_key == "gemini_key"
    assert settings.port == 8000
