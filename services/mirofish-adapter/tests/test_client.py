"""Tests for MiroFish HTTP client."""

import asyncio

import pytest
import respx
from httpx import AsyncClient

from xprclaw_mirofish.client import MiroFishClient
from xprclaw_mirofish.exceptions import MiroFishAPIError, MiroFishTimeoutError


@pytest.mark.asyncio
async def test_graph_build_success() -> None:
    """POST /api/graph/build returns project_id."""
    async with respx.mock:
        respx.post("http://localhost:5001/api/graph/build").mock(
            return_value=respx.MockResponse(200, json={"project_id": "proj_123"})
        )
        client = MiroFishClient()
        project_id = await client.graph_build("seed material")
        assert project_id == "proj_123"
        await client.close()


@pytest.mark.asyncio
async def test_graph_status_ready() -> None:
    """GET /api/graph/status returns status."""
    async with respx.mock:
        respx.get("http://localhost:5001/api/graph/status/proj_123").mock(
            return_value=respx.MockResponse(200, json={"status": "ready"})
        )
        client = MiroFishClient()
        status = await client.graph_status("proj_123")
        assert status["status"] == "ready"
        await client.close()


@pytest.mark.asyncio
async def test_wait_for_graph_success() -> None:
    """wait_for_graph polls until ready."""
    async with respx.mock:
        respx.get("http://localhost:5001/api/graph/status/proj_123").mock(
            side_effect=[
                respx.MockResponse(200, json={"status": "building"}),
                respx.MockResponse(200, json={"status": "ready"}),
            ]
        )
        client = MiroFishClient()
        await client.wait_for_graph("proj_123", poll_interval=0.01)
        await client.close()


@pytest.mark.asyncio
async def test_wait_for_graph_timeout() -> None:
    """wait_for_graph raises on deadline."""
    async with respx.mock:
        respx.get("http://localhost:5001/api/graph/status/proj_123").mock(
            return_value=respx.MockResponse(200, json={"status": "building"})
        )
        client = MiroFishClient()
        with pytest.raises(MiroFishTimeoutError):
            await client.wait_for_graph("proj_123", poll_interval=0.01, deadline=0.05)
        await client.close()


@pytest.mark.asyncio
async def test_simulation_start() -> None:
    """POST /api/simulation/start sends params."""
    async with respx.mock:
        respx.post("http://localhost:5001/api/simulation/start").mock(
            return_value=respx.MockResponse(200, json={})
        )
        client = MiroFishClient()
        await client.simulation_start("sim_123", max_rounds=50)
        await client.close()


@pytest.mark.asyncio
async def test_wait_for_simulation_success() -> None:
    """wait_for_simulation polls until completed."""
    async with respx.mock:
        respx.get("http://localhost:5001/api/simulation/status/sim_123").mock(
            side_effect=[
                respx.MockResponse(200, json={"state": "running"}),
                respx.MockResponse(200, json={"state": "completed"}),
            ]
        )
        client = MiroFishClient()
        await client.wait_for_simulation("sim_123", poll_interval=0.01)
        await client.close()


@pytest.mark.asyncio
async def test_wait_for_simulation_failure() -> None:
    """wait_for_simulation raises on failed state."""
    async with respx.mock:
        respx.get("http://localhost:5001/api/simulation/status/sim_123").mock(
            return_value=respx.MockResponse(200, json={"state": "failed", "error": "bad input"})
        )
        client = MiroFishClient()
        with pytest.raises(MiroFishAPIError, match="Simulation failed"):
            await client.wait_for_simulation("sim_123", poll_interval=0.01)
        await client.close()


@pytest.mark.asyncio
async def test_report_get() -> None:
    """GET /api/report/{id} fetches markdown."""
    async with respx.mock:
        respx.get("http://localhost:5001/api/report/rep_123").mock(
            return_value=respx.MockResponse(200, json={"markdown": "# Report\nContent"})
        )
        client = MiroFishClient()
        markdown = await client.report_get("rep_123")
        assert markdown == "# Report\nContent"
        await client.close()


@pytest.mark.asyncio
async def test_client_context_manager() -> None:
    """Client works as async context manager."""
    async with respx.mock:
        respx.post("http://localhost:5001/api/graph/build").mock(
            return_value=respx.MockResponse(200, json={"project_id": "proj_abc"})
        )
        async with MiroFishClient() as client:
            project_id = await client.graph_build("seed")
            assert project_id == "proj_abc"


@pytest.mark.asyncio
async def test_no_retry_on_400() -> None:
    """Client does not retry on 4xx errors."""
    async with respx.mock:
        respx.post("http://localhost:5001/api/graph/build").mock(
            return_value=respx.MockResponse(400, json={"error": "bad request"})
        )
        client = MiroFishClient()
        with pytest.raises(MiroFishAPIError):
            await client.graph_build("seed")
        await client.close()
