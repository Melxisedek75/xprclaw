"""Async HTTP client for MiroFish backend."""

import asyncio
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception,
    retry_if_result,
    stop_after_attempt,
    wait_exponential,
)

from xprclaw_mirofish.exceptions import MiroFishAPIError, MiroFishTimeoutError


class MiroFishClient:
    """Async HTTP client for MiroFish backend."""

    def __init__(
        self,
        base_url: str = "http://localhost:5001",
        timeout: float = 300.0,
        max_retries: int = 3,
    ):
        """Initialize client.

        Args:
            base_url: MiroFish backend URL
            timeout: Request timeout in seconds
            max_retries: Max retry attempts on transient errors
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "MiroFishClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create async client."""
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def _request(
        self, method: str, path: str, json: dict[str, Any] | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Make HTTP request with retries on transient errors."""

        def _is_retryable(exc: BaseException) -> bool:
            if isinstance(exc, httpx.HTTPStatusError):
                return exc.response.status_code >= 500
            return isinstance(exc, (httpx.NetworkError, httpx.TimeoutException))

        async def _request_once() -> dict[str, Any]:
            url = f"{self.base_url}{path}"
            try:
                response = await self.client.request(method, url, json=json, **kwargs)
                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    raise
                raise MiroFishAPIError(
                    f"HTTP {e.response.status_code}: {e.response.text}",
                    status_code=e.response.status_code,
                )
            except httpx.TimeoutException as e:
                raise MiroFishTimeoutError(f"Request timeout after {self.timeout}s") from e

        retry_count = 0
        async for attempt in AsyncRetrying(
            retry=retry_if_exception(_is_retryable),
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True,
        ):
            with attempt:
                try:
                    return await _request_once()
                except Exception:
                    retry_count = attempt.retry_state.attempt_number

        raise MiroFishAPIError(
            f"Request failed after {self.max_retries} retries",
            retry_count=retry_count,
        )

    async def graph_build(self, seed_material: str, project_name: str = "xprclaw") -> str:
        """POST /api/graph/build — submit seed, get project_id.

        Returns:
            project_id
        """
        response = await self._request(
            "POST",
            "/api/graph/build",
            json={"seed": seed_material, "project_name": project_name},
        )
        return response["project_id"]  # type: ignore[no-any-return]

    async def graph_status(self, project_id: str) -> dict[str, Any]:
        """GET /api/graph/status/{project_id} — poll until ready."""
        return await self._request("GET", f"/api/graph/status/{project_id}")

    async def simulation_prepare(
        self,
        project_id: str,
        personas: list[dict[str, Any]],
    ) -> str:
        """POST /api/simulation/prepare — generate profiles, get sim_id."""
        response = await self._request(
            "POST",
            "/api/simulation/prepare",
            json={"project_id": project_id, "personas": personas},
        )
        return response["simulation_id"]  # type: ignore[no-any-return]

    async def simulation_start(
        self,
        simulation_id: str,
        max_rounds: int = 30,
        platform: str = "xprclaw",
    ) -> None:
        """POST /api/simulation/start — start the actual simulation."""
        await self._request(
            "POST",
            "/api/simulation/start",
            json={
                "simulation_id": simulation_id,
                "max_rounds": max_rounds,
                "platform": platform,
            },
        )

    async def simulation_status(self, simulation_id: str) -> dict[str, Any]:
        """GET /api/simulation/status/{simulation_id} — poll."""
        return await self._request("GET", f"/api/simulation/status/{simulation_id}")

    async def simulation_stop(self, simulation_id: str) -> None:
        """POST /api/simulation/stop — cancel running simulation."""
        await self._request(
            "POST",
            "/api/simulation/stop",
            json={"simulation_id": simulation_id},
        )

    async def report_generate(self, simulation_id: str) -> str:
        """POST /api/report/generate — generate report, get report_id."""
        response = await self._request(
            "POST",
            "/api/report/generate",
            json={"simulation_id": simulation_id},
        )
        return response["report_id"]  # type: ignore[no-any-return]

    async def report_status(self, report_id: str) -> dict[str, Any]:
        """GET /api/report/status/{report_id} — poll."""
        return await self._request("GET", f"/api/report/status/{report_id}")

    async def report_get(self, report_id: str) -> str:
        """GET /api/report/{report_id} — fetch final report markdown."""
        response = await self._request("GET", f"/api/report/{report_id}")
        return response.get("markdown", "")  # type: ignore[no-any-return]

    async def wait_for_graph(
        self,
        project_id: str,
        poll_interval: float = 2.0,
        deadline: float = 600.0,
    ) -> None:
        """Poll until graph is ready, or raise timeout."""
        start_time = asyncio.get_event_loop().time()
        while True:
            status = await self.graph_status(project_id)
            if status.get("status") == "ready":
                return
            if asyncio.get_event_loop().time() - start_time > deadline:
                raise MiroFishTimeoutError(f"Graph build exceeded {deadline}s deadline")
            await asyncio.sleep(poll_interval)

    async def wait_for_simulation(
        self,
        simulation_id: str,
        poll_interval: float = 2.0,
        deadline: float = 600.0,
    ) -> None:
        """Poll until simulation finished, or raise on error/timeout."""
        start_time = asyncio.get_event_loop().time()
        while True:
            status = await self.simulation_status(simulation_id)
            state = status.get("state")
            if state == "completed":
                return
            if state == "failed":
                raise MiroFishAPIError(f"Simulation failed: {status.get('error', '')}")
            if asyncio.get_event_loop().time() - start_time > deadline:
                raise MiroFishTimeoutError(f"Simulation exceeded {deadline}s deadline")
            await asyncio.sleep(poll_interval)

    async def wait_for_report(
        self,
        report_id: str,
        poll_interval: float = 2.0,
        deadline: float = 600.0,
    ) -> None:
        """Poll until report is ready, or raise on error/timeout."""
        start_time = asyncio.get_event_loop().time()
        while True:
            status = await self.report_status(report_id)
            if status.get("status") == "ready":
                return
            if status.get("status") == "failed":
                raise MiroFishAPIError(f"Report generation failed: {status.get('error', '')}")
            if asyncio.get_event_loop().time() - start_time > deadline:
                raise MiroFishTimeoutError(f"Report generation exceeded {deadline}s deadline")
            await asyncio.sleep(poll_interval)

    async def close(self) -> None:
        """Cleanup."""
        if self._client:
            await self._client.aclose()
