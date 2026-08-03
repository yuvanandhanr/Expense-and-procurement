"""
Database Connection Verification Tests.

Validates the /ready readiness check against successful and degraded database states.
"""

from unittest.mock import AsyncMock
from fastapi.testclient import TestClient


def test_database_connection_success(
    client: TestClient, override_db: AsyncMock
) -> None:
    """
    Checks that /ready endpoint returns HTTP 200 and indicates success when DB is responsive.
    """
    # Mock database statement execution success
    override_db.execute.return_value = AsyncMock()

    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    override_db.execute.assert_called_once()


def test_database_connection_failure(
    client: TestClient, override_db: AsyncMock
) -> None:
    """
    Checks that /ready endpoint returns HTTP 503 Service Unavailable when DB connection fails.
    """
    # Force query execution to throw an exception
    override_db.execute.side_effect = Exception("DB Connection Timeout")

    response = client.get("/ready")
    assert response.status_code == 503
    data = response.json()
    assert "Database connection is offline" in data["detail"]
