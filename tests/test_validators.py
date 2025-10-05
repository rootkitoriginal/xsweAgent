"""
Tests for Pydantic field validators.
"""

import pytest
from pydantic import ValidationError

from src.config.settings import (CacheConfig, GeminiConfig, GitHubConfig,
                                 LoggingConfig, SecurityConfig)


class TestGitHubConfigValidator:
    """Test GitHubConfig validators."""

    def test_ensure_token_with_env_var(self, monkeypatch):
        """Test ensure_token validator with environment variable."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        config = GitHubConfig()
        assert config.token == "test_token"

    def test_ensure_token_with_value(self, monkeypatch):
        """Test ensure_token validator with direct value."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        config = GitHubConfig(token="direct_token")
        assert config.token == "direct_token"

    def test_ensure_token_missing(self, monkeypatch):
        """Test ensure_token validator raises when token is missing."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with pytest.raises(ValidationError) as exc_info:
            GitHubConfig()
        assert "GITHUB_TOKEN is required" in str(exc_info.value)


class TestGeminiConfigValidator:
    """Test GeminiConfig validators."""

    def test_validate_api_key_valid(self):
        """Test validate_api_key with valid key."""
        config = GeminiConfig(api_key="valid_api_key")
        assert config.api_key == "valid_api_key"

    def test_validate_api_key_none(self):
        """Test validate_api_key accepts None."""
        config = GeminiConfig(api_key=None)
        assert config.api_key is None

    def test_validate_api_key_placeholder(self):
        """Test validate_api_key rejects placeholder."""
        with pytest.raises(ValidationError) as exc_info:
            GeminiConfig(api_key="your_google_gemini_api_key_here")
        assert "Please replace the placeholder" in str(exc_info.value)


class TestCacheConfigValidator:
    """Test CacheConfig validators."""

    def test_validate_cache_type_valid(self):
        """Test validate_cache_type with valid types."""
        for cache_type in ["memory", "redis", "file"]:
            config = CacheConfig(type=cache_type)
            assert config.type == cache_type

    def test_validate_cache_type_invalid(self):
        """Test validate_cache_type with invalid type."""
        with pytest.raises(ValidationError) as exc_info:
            CacheConfig(type="invalid")
        assert "Cache type must be" in str(exc_info.value)


class TestLoggingConfigValidator:
    """Test LoggingConfig validators."""

    def test_validate_log_level_valid(self):
        """Test validate_log_level with valid levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = LoggingConfig(level=level)
            assert config.level == level

    def test_validate_log_level_case_insensitive(self):
        """Test validate_log_level normalizes case."""
        config = LoggingConfig(level="debug")
        assert config.level == "DEBUG"

    def test_validate_log_level_invalid(self):
        """Test validate_log_level with invalid level."""
        with pytest.raises(ValidationError) as exc_info:
            LoggingConfig(level="INVALID")
        assert "Log level must be one of" in str(exc_info.value)


class TestSecurityConfigValidator:
    """Test SecurityConfig validators."""

    def test_validate_secret_key_valid(self):
        """Test validate_secret_key with valid key."""
        config = SecurityConfig(secret_key="a" * 32)
        assert config.secret_key == "a" * 32

    def test_validate_secret_key_too_short(self):
        """Test validate_secret_key with short key."""
        with pytest.raises(ValidationError) as exc_info:
            SecurityConfig(secret_key="short")
        assert "at least 32 characters" in str(exc_info.value)

    def test_validate_secret_key_placeholder(self):
        """Test validate_secret_key rejects placeholder."""
        with pytest.raises(ValidationError) as exc_info:
            SecurityConfig(secret_key="your-super-secret-key-change-this-in-production")
        assert "Valid secret key is required" in str(exc_info.value)

    def test_validate_secret_key_empty(self):
        """Test validate_secret_key rejects empty key."""
        with pytest.raises(ValidationError) as exc_info:
            SecurityConfig(secret_key="")
        assert "Valid secret key is required" in str(exc_info.value)
