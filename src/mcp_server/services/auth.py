"""
MCP Server - Authentication
Authentication and authorization functionality.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from ...config import get_config
from ...config.logging_config import get_security_logger

logger = logging.getLogger(__name__)
security_logger = get_security_logger()

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> bool:
    """
    Verify API key authentication.

    Args:
        api_key: API key from header

    Returns:
        True if authenticated

    Raises:
        HTTPException: If authentication fails
    """
    settings = get_config()

    # If no API key is configured, allow access (dev mode)
    if not hasattr(settings, "api_key") or not settings.api_key:
        return True

    if not api_key:
        security_logger.log_authentication_attempt(
            user_id="unknown", success=False
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key != settings.api_key:
        security_logger.log_authentication_attempt(
            user_id="unknown", success=False
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    security_logger.log_authentication_attempt(
        user_id="api_key_user", success=True
    )
    return True


async def verify_bearer_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> bool:
    """
    Verify Bearer token authentication.

    Args:
        credentials: Bearer credentials

    Returns:
        True if authenticated

    Raises:
        HTTPException: If authentication fails
    """
    settings = get_config()

    # If no token is configured, allow access (dev mode)
    if not hasattr(settings, "bearer_token") or not settings.bearer_token:
        return True

    if not credentials:
        security_logger.log_authentication_attempt(
            user_id="unknown", success=False
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.credentials != settings.bearer_token:
        security_logger.log_authentication_attempt(
            user_id="unknown", success=False
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid bearer token",
        )

    security_logger.log_authentication_attempt(
        user_id="bearer_token_user", success=True
    )
    return True


async def optional_auth(
    api_key: Optional[str] = Security(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> bool:
    """
    Optional authentication - accepts API key or Bearer token.

    Args:
        api_key: Optional API key
        bearer: Optional Bearer token

    Returns:
        True if authenticated or no auth configured
    """
    settings = get_config()

    # If no auth is configured, allow access
    has_api_key_config = hasattr(settings, "api_key") and settings.api_key
    has_bearer_config = hasattr(settings, "bearer_token") and settings.bearer_token

    if not has_api_key_config and not has_bearer_config:
        return True

    # Try API key first
    if api_key and has_api_key_config:
        if api_key == settings.api_key:
            return True

    # Try Bearer token
    if bearer and has_bearer_config:
        if bearer.credentials == settings.bearer_token:
            return True

    # If auth is configured but neither worked, deny
    if has_api_key_config or has_bearer_config:
        security_logger.log_authentication_attempt(
            user_id="unknown", success=False
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    return True
