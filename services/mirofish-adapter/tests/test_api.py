"""Tests for FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from xprclaw_mirofish.api import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


def test_healthz(client: TestClient) -> None:
    """Test /healthz endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_root(client: TestClient) -> None:
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "xprclaw-mirofish"
    assert "version" in data
