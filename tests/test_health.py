"""
Health Endpoint Tests.

Validates application liveness (/health), system root (/), and application version (/version).
"""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient) -> None:
    """
    Checks that the root welcome message loads successfully.
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Welcome" in data["message"]
    assert "version" in data
    assert "environment" in data


def test_health_endpoint(client: TestClient) -> None:
    """
    Checks that the liveness check returns HTTP 200.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_version_endpoint(client: TestClient) -> None:
    """
    Checks that the version info endpoint loads successfully.
    """
    response = client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()
