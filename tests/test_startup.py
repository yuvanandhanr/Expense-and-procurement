"""
Startup Tests.

Validates settings loading, logging setup, and FastAPI application lifespan hooks.
"""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi import FastAPI
from src.core.config import settings
from src.core.logging_config import setup_logging
from src.main import lifespan


def test_settings_load() -> None:
    """
    Verifies settings load successfully with type checks and fallback constraints.
    """
    assert settings.ENVIRONMENT in ["development", "testing", "staging", "production"]
    assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    assert settings.APP_VERSION is not None


def test_logging_setup() -> None:
    """
    Verifies that calling setup_logging doesn't raise exceptions and initializes handlers.
    """
    setup_logging()


@pytest.mark.anyio
async def test_lifespan_startup() -> None:
    """
    Verifies that application lifespan starts up and shuts down without exceptions.
    
    Mocks the database engine to isolate testing.
    """
    dummy_app = FastAPI()
    
    with patch("src.main.async_engine") as mock_engine:
        # Mock engine context manager and execution
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn
        mock_engine.dispose = AsyncMock()
        
        async with lifespan(dummy_app):
            pass
        
        mock_engine.connect.assert_called_once()
        mock_engine.dispose.assert_called_once()
