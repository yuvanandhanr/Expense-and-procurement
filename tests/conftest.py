"""
Pytest Configuration.

Sets up test clients, test environments, and dependency override fixtures
for validating the FastAPI application skeleton.
"""

import sys
from unittest.mock import MagicMock
# Mock pandas to bypass Windows Application Control blocking pandas DLLs
sys.modules['pandas'] = MagicMock()

from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.main import app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """
    Specifies asyncio backend for anyio/pytest tests.
    """
    return "asyncio"


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """
    Synchronous TestClient fixture.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Asynchronous HTTPX test client using ASGITransport mapping to the FastAPI app.
    """
    # Use ASGITransport for modern HTTPX async testing
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """
    Mocks a SQLAlchemy AsyncSession for isolating connection checks.
    """
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.close = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def override_db(mock_db_session: AsyncMock) -> Generator[AsyncMock, None, None]:
    """
    Overrides get_db_session dependency in the FastAPI application with a mock session.
    """
    async def _get_db_override():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = _get_db_override
    yield mock_db_session
    app.dependency_overrides.pop(get_db_session, None)
