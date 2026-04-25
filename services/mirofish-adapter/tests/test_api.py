"""Tests for FastAPI application."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

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


def test_simulate_invalid_request() -> None:
    """POST /v1/simulate with invalid request returns 422."""
    client = TestClient(app)
    response = client.post(
        "/v1/simulate",
        json={"invalid_field": "value"},
    )
    assert response.status_code == 422


@pytest.mark.skip(reason="Requires MiroFish backend or proper async initialization")
def test_simulate_success() -> None:
    """POST /v1/simulate endpoint is wired correctly (integration test requires MiroFish)."""
    pass
